import random
import time

from typing import Optional

from constants import ROUTES
from src.logger import CustomLogger
from src.web3_client import AsyncWeb3Account
from src.request_client import AsyncHttpClient
from utils.random_utils import get_random_route
from utils.web3_utils import generate_contract_address, generate_calldata
from utils.request_utils import get_set_cookie_headers, get_favicon_headers, get_airdrop_request_headers


class RomeLabsClient:
    def __init__(
            self,
            private_key: str,
            rpc_url: str,
            explorer_url: str,
            headers: dict,
            logger_id: int = "",
            proxy_url: Optional[str] = None,
            retry_attempts: int = 3,
            timeout_429: int = 60,
    ):

        self.http_client = AsyncHttpClient(
            base_url=None, proxy=proxy_url, retry_attempts=retry_attempts, timeout_429=timeout_429,
            _default_headers=headers
        )

        self.web3_account = AsyncWeb3Account(private_key, rpc_url, explorer_url, proxy_url)

        self.proxy_url = proxy_url
        self.wallet_address = self.web3_account.get_wallet_address()
        self.logger = CustomLogger(id=logger_id).get_logger()

    async def close_session(self):
        await self.http_client.close()

    async def get_set_cookie(self) -> str:
        headers = get_set_cookie_headers()
        url = "https://rome.testnet.romeprotocol.xyz/request_airdrop"

        response = await self.http_client.get(url, headers=headers, fetch_response=False)

        if "Set-Cookie" in response["headers"]:
            set_cookie = response["headers"]["Set-Cookie"]
            return set_cookie
        raise RuntimeError("Set-Cookie header not found in the response 111!")

    async def get_favicon(self):
        set_cookie = await self.get_set_cookie()
        headers = get_favicon_headers(set_cookie)
        url = "https://rome.testnet.romeprotocol.xyz/favicon.ico"

        response = await self.http_client.get(url, headers=headers, fetch_response=False)

        if "Set-Cookie" in response["headers"]:
            set_cookie = response["headers"]["Set-Cookie"]
            return set_cookie
        raise RuntimeError("Set-Cookie header not found in the response!")

    async def send_airdrop_request(self, amount: str, captcha_response: str):
        set_cookie = await self.get_favicon()
        headers = get_airdrop_request_headers(set_cookie)

        payload = {
            "recipientAddr": self.wallet_address,
            "amount": amount,
            "captchaResponse": captcha_response,
        }

        url = "https://rome.testnet.romeprotocol.xyz/airdrop"

        print(url)

        response = await self.http_client.post(
            url, headers=headers, json=payload, fetch_response=False
        )

        print(response)

        return response

    async def deploy_hello_world_contract(self, compiled_sol: dict) -> bool:
        bytecode = compiled_sol["contracts"]["HelloWorld.sol"]["HelloWorld"]["evm"]["bytecode"]["object"]
        abi = compiled_sol["contracts"]["HelloWorld.sol"]["HelloWorld"]["abi"]

        contract = await self.web3_account.make_contract(abi=abi, bytecode=bytecode)
        tx_data = await self.web3_account.get_data_for_tx(increase_factor=1.5)
        gas_price = int((await self.web3_account.get_gas_price()) * 1.5)

        transaction = await contract.constructor().build_transaction(
            {
                "chainId": tx_data["chainId"],
                "gasPrice": gas_price,
                "from": self.wallet_address,
                "nonce": tx_data["nonce"],
            }
        )

        transaction['gas'] = await self.web3_account.get_estimate_gas(transaction)

        return await self.web3_account.send_transaction(transaction)

    async def deploy_own_tokens(self) -> bool:
        tx_data = await self.web3_account.get_data_for_tx(increase_factor=1.5)
        generate_contract_address(self.wallet_address, tx_data['nonce'])

        transaction = {
            "from": self.wallet_address,
            "data": generate_calldata(),
            "maxPriorityFeePerGas": tx_data["max_priority_fee_per_gas"],
            "maxFeePerGas": tx_data["max_fee_per_gas"],
            "nonce": tx_data["nonce"],
            "gas": 500000,
            "chainId": tx_data["chainId"],
        }

        return await self.web3_account.send_transaction(transaction)

    async def get_random_amount_to_transfer(self) -> int:
        full_balance = await self.web3_account.get_balance()
        random_percentage = random.uniform(0.01, 0.15)
        self.transaction_amount = int(full_balance * random_percentage)
        return self.transaction_amount

    async def prepare_transfer_tx(self) -> bool:
        tx_data = await self.web3_account.get_data_for_tx(increase_factor=1.5)
        value = await self.get_random_amount_to_transfer()
        generated_wallet = await self.web3_account.generate_wallet()

        transaction = {
            "from": self.wallet_address,
            "to": generated_wallet,
            "value": value,
            "maxPriorityFeePerGas": tx_data["max_priority_fee_per_gas"],
            "maxFeePerGas": tx_data["max_fee_per_gas"],
            "nonce": tx_data["nonce"],
            "chainId": tx_data["chainId"],
        }

        transaction["gas"] = await self.web3_account.get_estimate_gas(transaction) + 30000

        return await self.web3_account.send_transaction(transaction)


    def generate_swap_calldata(self) -> str:
        timestamp = int(time.time() * 1000)
        route = get_random_route(ROUTES)

        types = ['uint256', 'address[]', 'address', 'uint256']
        params = [
            0,
            route,
            self.wallet_address,
            timestamp
        ]

        function_selector = '0x7ff36ab5'

        return self.web3_account.encode_calldata(function_selector, types, params)


    async def swap(self):
        tx_data = await self.web3_account.get_data_for_tx(increase_factor=1.5)
        value = await self.get_random_amount_to_transfer()

        transaction = {
            "from": self.wallet_address,
            "to": "0x3696d3bc61E78e8EC9E8A35865c6681d7Dd0c49d",
            "data": self.generate_swap_calldata(),
            "value": value,
            "maxPriorityFeePerGas": tx_data["max_priority_fee_per_gas"],
            "maxFeePerGas": tx_data["max_fee_per_gas"],
            "nonce": tx_data["nonce"],
            "chainId": tx_data["chainId"],

        }
        transaction["gas"] = await self.web3_account.get_estimate_gas(transaction) + 50000

        return await self.web3_account.send_transaction(transaction)
