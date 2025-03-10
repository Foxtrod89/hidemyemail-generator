from rookiepy import safari, chrome, firefox
from typing import List, Dict
from rich.console import Console

class CookiesManager():
    def __init__(self):
        self.console = Console()
        self.browser_map = {
                   "safari": safari,
                   "chrome":chrome,
                   "firefox":firefox,
                  }

    def _get_cookies_from_browser(self, browser: str, domain: str) -> List[dict]:
        browser_selected = self.browser_map.get(browser)
        if not browser_selected:
            raise ValueError(f"Browser {browser}'is not supported!")
        try: 
            return browser_selected([domain])  
        except RuntimeError as e:
            raise RuntimeError(f"Failed to fetch cookies for {browser}.") from e
 
    def _cookies_formatter(self, cookies: List[Dict[str, str]]) -> str:
        raw_cookie_string = ""
        for cookie in cookies:
            if cookie['name'].startswith('X-APPLE') or cookie['name'].startswith('X_APPLE'):
                raw_cookie_string += f"{cookie['name']}={cookie['value']};"
        return raw_cookie_string
    
    def cookie_writer(self, browser: str) -> None:
        try:
            cookies = self._get_cookies_from_browser(browser,'.icloud.com')
            formatted_cookies = self._cookies_formatter(cookies)
            if not formatted_cookies:
                self.console.log(f":x: No valid cookies found for {browser}. Skipping file write.")
                return
            with open('cookie.txt', 'w', encoding="utf-8") as fo:
                fo.write(formatted_cookies)
            self.console.log(f":white_check_mark: Cookies successfully written to [italic]cookie.txt[/] from {browser}.") 
        except Exception as e:
            self.console.log(f":x: Failed to write cookies for {browser}: {e}")
