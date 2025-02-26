import asyncio
import datetime
import os
from typing import Union, List, Optional
import re
from rich.text import Text
from rich.prompt import IntPrompt
from rich.console import Console
from rich.table import Table
from rich.box import MINIMAL_HEAVY_HEAD
from rookiepy import safari, chrome, firefox
from icloud import HideMyEmail
import logging

logging.basicConfig(level=logging.INFO)
MAX_CONCURRENT_TASKS = 10


class RichHideMyEmail(HideMyEmail):
    _cookie_file = "cookie.txt"

    def __init__(self, label:Optional[str], notes: Optional[str]):
        super().__init__(label=label, notes=notes)
        self.console = Console()
        self.table = Table(box=MINIMAL_HEAVY_HEAD,
                           padding=(0,0,1,0), # top, right, bottom, and left borders
                        )

        if os.path.exists(self._cookie_file):
            # load in a cookie string from file
            with open(self._cookie_file, "r") as f:
                self.cookies = [line for line in f if not line.startswith("//")][0]
        else:
            self.console.log(
                '[bold yellow][WARN][/] No "cookie.txt" file found! Generation might not work due to unauthorized access.'
            )

    async def _generate_one(self) -> Union[str, None]:
        # First, generate an email
        gen_res = await self.generate_email()

        if not gen_res:
            return
        elif "success" not in gen_res or not gen_res["success"]:
            error = gen_res["error"] if "error" in gen_res else {}
            err_msg = "Unknown"
            if type(error) == int and "reason" in gen_res:
                err_msg = gen_res["reason"]
            elif type(error) == dict and "errorMessage" in error:
                err_msg = error["errorMessage"]
            self.console.log(
                f"[bold red][ERR][/] - Failed to generate email. Reason: {err_msg}"
            )
            return

        email = gen_res["result"]["hme"]
        self.console.log(f'[50%] "{email}" - Successfully generated')

        # Then, reserve it
        reserve_res = await self.reserve_email(email)

        if not reserve_res:
            return
        elif "success" not in reserve_res or not reserve_res["success"]:
            error = reserve_res["error"] if "error" in reserve_res else {}
            err_msg = "Unknown"
            if type(error) == int and "reason" in reserve_res:
                err_msg = reserve_res["reason"]
            elif type(error) == dict and "errorMessage" in error:
                err_msg = error["errorMessage"]
            self.console.log(
                f'[bold red][ERR][/] "{email}" - Failed to reserve email. Reason: {err_msg}'
            )
            return

        self.console.log(f'[100%] "{email}" - Successfully reserved')
        return email

    async def _generate(self, num: int):
        tasks = []
        for _ in range(num):
            task = asyncio.ensure_future(self._generate_one())
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
            return

        if "success" not in gen_res or not gen_res["success"]:
            error = gen_res["error"] if "error" in gen_res else {}
            err_msg = "Unknown"
            if type(error) == int and "reason" in gen_res:
                err_msg = gen_res["reason"]
            elif type(error) == dict and "errorMessage" in error:
                err_msg = error["errorMessage"]
            self.console.log(
                f"[bold red][ERR][/] - Failed to generate email. Reason: {err_msg}"
            )
            return

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


async def generate(count: Optional[int], label:Optional[str], notes: Optional[str]) -> None:
    async with RichHideMyEmail(label, notes) as hme:
        await hme.generate(count)


async def list(active: bool, search: str, label: Optional[str], notes: Optional[str]) -> None:
    async with RichHideMyEmail(label, notes) as hme:
        await hme.list(active, search)


def _get_cookies_from_browser(browser: str, domain: str) -> List[dict]:
    browser_map = {"safari": safari,
                   "chrome":chrome,
                   "firefox":firefox,
                    }
    browser_selected = browser_map.get(browser)
    if not browser_selected:
        raise Exception(f"Browser {browser}' not supported!")
    try: 
        cookies = browser_selected([domain])
        return cookies    
    except RuntimeError:
        print(f"Unable to fetch cookies from browser {browser}!")
        exit(1)
        
def _cookies_formatter(cookies: List[dict]) -> str:
    raw_cookie_string = ""
    for cookie in cookies:
        if cookie['name'].startswith('X-APPLE') or cookie['name'].startswith('X_APPLE'):
            raw_cookie_string += f"{cookie['name']}={cookie['value']};"
    return raw_cookie_string

def cookie_writer(browser: str) -> None:
    with open('cookie.txt', 'w') as fo:
        fo.write(_cookies_formatter(_get_cookies_from_browser(browser,'.icloud.com')))
        logging.info(f"Cookies successfully written to cookie.txt for {browser}.")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(generate(None, None, None))
    except KeyboardInterrupt:
        pass
