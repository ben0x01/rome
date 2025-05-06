import asyncio
import time
from src.request_client import AsyncHttpClient
from curl_cffi.requests import AsyncSession

class CaptchaSolver(AsyncSession):
    def __init__(self, api_key: str, headers: dict, proxy_url: str = None, **kwargs) -> None:
        self.http_client = AsyncHttpClient(
            base_url=None, proxy=proxy_url,
            _default_headers=headers, **kwargs
        )

        super().__init__(
            base_url=None,
            proxy=proxy_url,
            verify=False,
            allow_redirects=True,
            trust_env=True,
            **kwargs,
        )
        self.api_key = api_key


    async def create_task_for_captcha(self) -> str:
        url = 'https://api.capsolver.com/createTask'
        payload = {
            "clientKey": self.api_key,
            "task": {
                "type": "ReCaptchaV2Task",
                "websiteURL": "https://rome.testnet.romeprotocol.xyz/request_airdrop",
                "websiteKey": "6Leq7o0qAAAAAKC0I6TptEAo6QxUcbv7_WFA1Ly9",
            }
        }

        response = await self.http_client.post(url, json=payload)
        if response.get('errorId') == 0:
            task_id = response.get('taskId')
            if task_id:
                return task_id
            else:
                raise RuntimeError("Task ID not found in the response.")
        else:
            error_description = response.get('errorDescription', 'Unknown error')
            raise RuntimeError(f"Error creating task: {error_description}")


    async def get_captcha_key(self, task_id) ->str:
        url = 'https://api-stable.capsolver.com/getTaskResult'
        payload = {
            "clientKey": self.api_key,
            "taskId": task_id,
        }

        print(payload)

        total_time = 0
        timeout = 360
        poll_interval = 5

        while True:
            response = await self.http_client.post(url, json=payload)

            print(response)

            if response.get('errorId') != 0:
                error_description = response.get('errorDescription', 'Unknown error')
                raise RuntimeError(f"Error getting task result: {error_description}")

            if response.get('status') == 'ready':
                solution = response.get('solution', {})
                captcha_response = solution.get('gRecaptchaResponse')
                if captcha_response:
                    return captcha_response
                raise RuntimeError("Captcha solution not found in the response.")

            total_time += poll_interval
            await asyncio.sleep(poll_interval)
            if total_time > timeout:
                raise RuntimeError("Failed to solve captcha within 360 seconds.")