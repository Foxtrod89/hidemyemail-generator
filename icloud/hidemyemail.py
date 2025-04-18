import asyncio
import aiohttp
import ssl
import certifi
from typing import Callable, Optional, Union


class HideMyEmail:
    base_url_v1 = "https://p68-maildomainws.icloud.com/v1/hme"
    base_url_v2 = "https://p68-maildomainws.icloud.com/v2/hme"
    params = {
        "clientBuildNumber": "2413Project28",
        "clientMasteringNumber": "2413B20",
        "clientId": "",
        "dsid": "",  # Directory Services Identifier (DSID) is a method of identifying AppleID accounts
    }

    def __init__(self, label: Optional[str], notes: Optional[str], cookies: str = ""):
        """Initializes the HideMyEmail class.

        Args:
            label (str)     Label that will be set for all emails generated, defaults to `rtuna's gen`
            cookies (str)   Cookie string to be used with requests. Required for authorization.
        """
        # Label that will be set for all emails generated, defaults to `rtuna's gen`
        self.label = label

        self.notes = notes

        # Cookie string to be used with requests. Required for authorization.
        self.cookies = cookies

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            ssl_context=ssl.create_default_context(cafile=certifi.where())
        )
        self.s = aiohttp.ClientSession(
            headers={
                "Connection": "keep-alive",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Content-Type": "text/plain",
                "Accept": "*/*",
                "Sec-GPC": "1",
                "Origin": "https://www.icloud.com",
                "Sec-Fetch-Site": "same-site",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": "https://www.icloud.com/",
                "Accept-Language": "en-US,en-GB;q=0.9,en;q=0.8,cs;q=0.7",
                "Cookie": self.__cookies.strip(),
            },
            timeout=aiohttp.ClientTimeout(total=10),
            connector=connector,
        )

        return self

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        await self.s.close()

    @property
    def cookies(self) -> str:
        return self.__cookies

    @cookies.setter
    def cookies(self, cookies: str):
        # remove new lines/whitespace for security reasons
        self.__cookies = cookies.strip()

    async def generate_email(self) -> dict:
        """Generates an email"""
        try:
            async with self.s.post(
                f"{self.base_url_v1}/generate",
                params=self.params,
                json={"langCode": "en-us"},
            ) as resp:
                res = await resp.json()
                return res
        except asyncio.TimeoutError:
            return {"error": 1, "reason": "Request timed out"}
        except Exception as e:
            return {"error": 1, "reason": str(e)}

    async def reserve_email(self, email: str) -> dict:
        """Reserves an email and registers it for forwarding"""
        try:
            payload = {
                "hme": email,
                "label": self.label,
                "note": self.notes,
            }
            async with self.s.post(
                f"{self.base_url_v1}/reserve", params=self.params, json=payload
            ) as resp:
                res = await resp.json()
            return res
        except asyncio.TimeoutError:
            return {"error": 1, "reason": "Request timed out"}
        except Exception as e:
            return {"error": 1, "reason": str(e)}

    async def list_email(self) -> dict:
        """List all HME"""
        try:
            async with self.s.get(
                f"{self.base_url_v2}/list", params=self.params
            ) as resp:
                res = await resp.json()
                return res
        except asyncio.TimeoutError:
            return {"error": 1, "reason": "Request timed out"}
        except Exception as e:
            return {"error": 1, "reason": str(e)}

    async def delete_email(self, anonymousId: str) -> dict:
        """Delete email"""
        try:
            async with self.s.post(
                f"{self.base_url_v1}/delete",
                params=self.params,
                json={"anonymousId": anonymousId},
            ) as resp:
                res = await resp.json()
                return res
        except asyncio.TimeoutError:
            return {"error": 1, "reason": "Request timed out"}
        except Exception as e:
            return {"error": 1, "reason": str(e)}

    async def deactivate_email(self, anonymousId: str) -> dict:
        """Deactivate emails for forwarding"""
        try:
            async with self.s.post(
                f"{self.base_url_v1}/deactivate",
                params=self.params,
                json={"anonymousId": anonymousId},
            ) as resp:
                res = await resp.json()
                return res
        except asyncio.TimeoutError:
            return {"error": 1, "reason": "Request timed out"}
        except Exception as e:
            return {"error": 1, "reason": str(e)}

    async def reactivate_email(self, anonymousId: str) -> dict:
        """Reactivate emails for forwarding"""
        try:
            async with self.s.post(
                f"{self.base_url_v1}/reactivate",
                params=self.params,
                json={"anonymousId": anonymousId},
            ) as resp:
                res = await resp.json()
                return res
        except asyncio.TimeoutError:
            return {"error": 1, "reason": "Request timed out"}
        except Exception as e:
            return {"error": 1, "reason": str(e)}
