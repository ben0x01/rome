from enum import Enum
from random import choice


class ImpersonateOs(Enum):
    MACOS = "macOS"
    WINDOWS = "Windows"

    @classmethod
    def from_str(cls, s: str) -> 'ImpersonateOs':
        return cls(s)

    def to_str(self) -> str:
        return self.value

    def user_agent_os(self) -> str:
        if self == ImpersonateOs.MACOS:
            return "(Macintosh; Intel Mac OS X 10_15_7)"
        elif self == ImpersonateOs.WINDOWS:
            return "(Windows NT 10.0; Win64; x64)"

    @classmethod
    def random(cls) -> 'ImpersonateOs':
        return choice(list(cls))


class Impersonate(Enum):
    CHROME_120 = "120.0.0.0"
    CHROME_123 = "123.0.0.0"
    CHROME_124 = "124.0.0.0"
    CHROME_126 = "126.0.0.0"
    CHROME_127 = "127.0.0.0"
    CHROME_128 = "128.0.0.0"
    CHROME_129 = "129.0.0.0"
    CHROME_130 = "130.0.0.0"
    CHROME_131 = "131.0.0.0"

    @classmethod
    def from_str(cls, s: str) -> 'Impersonate':
        return cls(s)

    def to_str(self) -> str:
        return self.value

    def ua(self) -> str:
        ua_mapping = {
            Impersonate.CHROME_120: '"Chromium";v="120", "Google Chrome";v="120", "Not?A_Brand";v="99"',
            Impersonate.CHROME_123: '"Google Chrome";v="123", "Not;A=Brand";v="8", "Chromium";v="123"',
            Impersonate.CHROME_124: '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            Impersonate.CHROME_126: '"Chromium";v="126", "Google Chrome";v="126", "Not-A.Brand";v="99"',
            Impersonate.CHROME_127: '"Not/A)Brand";v="8", "Chromium";v="127", "Google Chrome";v="127"',
            Impersonate.CHROME_128: '"Chromium";v="128", "Google Chrome";v="128", "Not?A_Brand";v="99"',
            Impersonate.CHROME_129: '"Google Chrome";v="129", "Chromium";v="129", "Not_A Brand\";v="24"',
            Impersonate.CHROME_130: '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            Impersonate.CHROME_131: '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand\";v="24"'
        }
        return ua_mapping[self]

    def user_agent(self, os: ImpersonateOs) -> str:
        user_agent_os = os.user_agent_os()
        version = self.to_str()
        return f"Mozilla/5.0 {user_agent_os} AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"

    def headers(self, os: ImpersonateOs) -> dict:
        return {
            "User-Agent": self.user_agent(os),
            "sec-ch-ua": self.ua(),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": f'"{os.to_str()}"'
        }

    @classmethod
    def random(cls) -> 'Impersonate':
        return choice(list(cls))


def generate_random_impersonation() -> tuple[ImpersonateOs, Impersonate]:
    random_os = ImpersonateOs.random()
    random_version = Impersonate.random()
    return random_os, random_version




def get_set_cookie_headers() -> dict:
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                  "image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.7",
        "Cache-Control": "max-age=0",
        "Host": "rome.testnet.romeprotocol.xyz",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }


def get_favicon_headers(set_cookies: str) -> dict:
    return {
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Cookie": set_cookies,
        "Host": "rome.testnet.romeprotocol.xyz",
        "Referer": "https://rome.testnet.romeprotocol.xyz/request_airdrop",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-origin",
    }


def get_airdrop_request_headers(favicon_cookie: str) -> dict:
    return {
        "Cookie": favicon_cookie,
        "Host": "rome.testnet.romeprotocol.xyz",
        "Origin": "https://rome.testnet.romeprotocol.xyz",
        "Referer": "https://rome.testnet.romeprotocol.xyz/request_airdrop",
    }
