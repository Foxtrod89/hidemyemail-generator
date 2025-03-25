import rookiepy
from typing import List, Dict, Union
from rich.console import Console
from sys import platform

class CookiesManager():
    def __init__(self):
        self.console = Console()
        self.browser_map = ["chrome","firefox"]
        if platform == 'darwin':
            self.browser_map.append('safari')
        elif platform == 'win32':
            self.browser_map.append('internet_explorer')

    def _get_cookies_from_browser(self, browser: str, domain: str) -> Union[List[Dict[str,str]], None]:
        if browser not in self.browser_map: 
            self.console.log(
                             f"[bold red][ERR][/]"
                             f"You can not use browser [italic][bold yellow]{browser}[/][/]" 
                             f" on platform [italic][bold yellow]{platform}[/][/]"
                             )
            return
        browser_object = getattr(rookiepy, browser)
        return browser_object([domain])  
 
    def _cookies_formatter(self, cookies: List[Dict[str, str]]) -> str:
        return ";".join(
                        f"{cookie['name']}={cookie['value']}"
                        for cookie in cookies
                        if cookie.get('name', '').startswith(('X-APPLE', 'X_APPLE'))
        )

    def cookie_writer(self, browser: str) -> None:
        try:
            cookies = self._get_cookies_from_browser(browser,'.icloud.com')
            if not cookies:
                self.console.log(f":x: No valid cookies found for {browser}. Skipping file write.")
                return
            formatted_cookies = self._cookies_formatter(cookies)
            with open('cookie.txt', 'w', encoding="utf-8") as fo:
                fo.write(formatted_cookies)
            self.console.log(f":white_check_mark: Cookies successfully written to [italic]cookie.txt[/] from [italic]{browser}[/].") 
        except Exception as e:
            self.console.log(f":x: Failed to write cookies for [italic]{browser}[/]: {e}")
