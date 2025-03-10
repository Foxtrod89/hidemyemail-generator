import asyncio
import datetime
import os
from typing import List, Optional, Awaitable, Callable
import re
from rich.text import Text
from rich.prompt import IntPrompt
from rich.console import Console
from rich.table import Table
from rich.box import MINIMAL_HEAVY_HEAD
from icloud import HideMyEmail

MAX_CONCURRENT_TASKS = 5


class RichHideMyEmail(HideMyEmail):
    _cookie_file = "cookie.txt"

    def __init__(self, label:Optional[str], notes: Optional[str]):
        super().__init__(label=label, notes=notes)
        self.console = Console()
        self.table = Table(box=MINIMAL_HEAVY_HEAD,
                           padding=(0,0,1,0), # top, right, bottom, and left borders
                        )

        if os.path.exists(self._cookie_file) and os.path.getsize(self._cookie_file) > 1:
            # load in a cookie string from file
            with open(self._cookie_file, "r") as f:
                self.cookies = [line for line in f if not line.startswith("//")][0]
        else:
            self.console.log(
                '[bold yellow][WARN][/] No "cookie.txt" file found OR file maybe empty! Generation will not work due to unauthorized access'
            )
            exit(1)
    
    async def _log_email_error(
            self,
            gen_res: Optional[dict],
            hme: str="",
            action_name: str="",
            target: str= "email"
            ) -> None:
        if not gen_res:
            return
        error = gen_res.get("error", {})
        err_msg = gen_res.get("reason", "Unknown") if isinstance(error, int) else error.get("errorMessage", "Unknown")
        self.console.log(
        f"[bold red][ERR][/]"
        f"- Failed to {action_name} [italic]{target}[/] for [italic][red]{hme}[/][/]. "
        f"Reason: {err_msg}"
    )

    async def _generate_one(self) -> Optional[str]:
        # First, generate an email
        gen_res = await self.generate_email()
        if not gen_res:
            await self._log_email_error(gen_res, action_name="get", target="generate")
        email = gen_res["result"]["hme"]
        self.console.log(f'[50%] "{email}" - Successfully generated')
        # Then, reserve it
        reserve_res = await self.reserve_email(email)
        if not reserve_res:
            await self._log_email_error(reserve_res, action_name="get", target="reserve") 
        self.console.log(f'[100%] "{email}" - Successfully reserved')
        return email

    async def _generate(self, num: int):
        tasks = []
        for _ in range(num):
            task = asyncio.create_task(self._generate_one())
            tasks.append(task)
        return filter(lambda e: e is not None, await asyncio.gather(*tasks))

    async def generate(self, count: Optional[int]) -> List[str]:
        try:
            emails = []
            self.console.rule()
            if count is None:
                s = IntPrompt.ask(
                    Text.assemble(("How many iCloud emails you want to generate?")),
                    console=self.console,
                )
                count = int(s)
            self.console.log(f"Generating {count} email(s)...")
            self.console.rule()
            with self.console.status(f"[bold green]Generating iCloud email(s)..."):
                while count > 0:
                    batch = await self._generate(
                        count if count < MAX_CONCURRENT_TASKS else MAX_CONCURRENT_TASKS
                    )
                    count -= MAX_CONCURRENT_TASKS
                    emails += batch
            if len(emails) > 0:
                with open("emails.txt", "a+") as f:
                    f.write(os.linesep.join(emails) + os.linesep)
                self.console.rule()
                self.console.log(
                    f':star: Emails have been saved into the "emails.txt" file'
                )
                self.console.log(
                    f"[bold green]All done![/] Successfully generated [bold green]{len(emails)}[/] email(s)"
                )
            return emails
        except KeyboardInterrupt:
            return []

    async def list(self, active: bool, search: str) -> None:
        gen_res = await self.list_email()
        if not gen_res:
            await self._log_email_error(gen_res, action_name="get", target="list")
        self.table.add_column("Label", no_wrap=True)
        self.table.add_column("Notes")
        self.table.add_column("Hide my email", no_wrap=True)
        self.table.add_column("Created Date Time")
        self.table.add_column("IsActive")
        for row in gen_res["result"]["hmeEmails"]:
            if search is not None and re.search(search, row["label"], flags=re.IGNORECASE):
                    raw_time =datetime.datetime.fromtimestamp(row["createTimestamp"] / 1000) 
                    self.table.add_row(
                        row["label"],
                        row["note"],
                        row["hme"],
                        str(raw_time.replace(microsecond=0)),
                        str(row["isActive"]),
                    )
            if row["isActive"] == active and search is None:
                    raw_time =datetime.datetime.fromtimestamp(row["createTimestamp"] / 1000)
                    self.table.add_row(
                        row["label"],
                        row["note"],
                        row["hme"],
                        str(raw_time.replace(microsecond=0)),
                        str(row["isActive"]),
                    )
        self.console.print(self.table)
              
    async def _get_anonymousid(self, hme:str) -> Optional[str]:
        # anonymousid needed as payload for delete, deactivate, reactivate endpoints
        gen_res = await self.list_email()
        if not gen_res:
            await self._log_email_error(gen_res, hme, action_name="get", target="anonymousId")
        try:
            for row in gen_res["result"]["hmeEmails"]:
                if row.get('hme') == hme:
                    return row.get('anonymousId')
            self.console.log(
                             f"[bold red][ERR][/] - No [italic][green]anonymousId[/][/] "
                             f"found for [italic][green]{hme}[/][/], "
                             f"make sure email exist!"
                             )
            return None
        except KeyError as e:
            self.console.log(f"[bold red][ERR][/] - KeyError: {str(e)}.")
        return None

    async def _handle_email_action(
    self, 
    hme: str, 
    action_func: Callable[[str], Awaitable[Optional[dict]]], 
    action_name: str
    ) -> None:
        """Generic function"""
        hme = hme.strip()
        anonymous_id = await self._get_anonymousid(hme)
        if anonymous_id is None:
            return
        gen_res = await action_func(anonymous_id)
        if not gen_res or not gen_res.get("success"):
            await self._log_email_error(gen_res, hme, action_name)
            return 
        self.console.log(f"Email: [italic][bright_blue]{hme}[/][/] was successfully {action_name}")
    
    async def _delete_one(self, hme: str) -> None:
            await self._handle_email_action(hme, self.delete_email, "delete")

    async def delete(self, hmes: List[str]) -> None:
            tasks = [asyncio.create_task(self._delete_one(hme)) for hme in hmes]
            await asyncio.gather(*tasks)

    async def _deactivate_one(self, hme: str) -> None:
        await self._handle_email_action(hme, self.deactivate_email, "disable for forwarding")

    async def deactivate(self, hmes: List[str]) -> None:
        tasks = [asyncio.create_task(self._deactivate_one(hme)) for hme in hmes]    
        await asyncio.gather(*tasks)
    
    async def _reactivate_one(self, hme: str) -> None:
        await self._handle_email_action(hme, self.reactivate_email, "enable for forwarding")
        
    async def reactivate(self, hmes: List[str]) -> None:
        tasks = [asyncio.create_task(self._reactivate_one(hme)) for hme in hmes]
        await asyncio.gather(*tasks)


async def generate(count: Optional[int], label:Optional[str], notes: Optional[str]) -> None:
    async with RichHideMyEmail(label, notes) as hme:
        await hme.generate(count)

async def list(active: bool, search: str, label: Optional[str], notes: Optional[str]) -> None:
    async with RichHideMyEmail(label, notes) as hme:
        await hme.list(active, search)

async def delete(email: List[str]) -> None:
    async with RichHideMyEmail("","") as hme:
        await hme.delete(email)

async def deactivate(email: List[str]) -> None:
    async with RichHideMyEmail("","") as hme:
        await hme.deactivate(email)

async def reactivate(email: List[str]) -> None:
    async with RichHideMyEmail("","") as hme:
        await hme.reactivate(email)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(generate(None, None, None))
    except KeyboardInterrupt:
        pass
