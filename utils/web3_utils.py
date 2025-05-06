from rlp import encode
from web3 import AsyncWeb3
from eth_utils import keccak
from web3.types import HexStr

from utils.random_utils import generate_random_string, need_to_generate_random_symbol
from constants import PART_OF_CALL_DATA, DEFAULT_LINE


def generate_contract_address(sender: HexStr, nonce: int) -> str:
    sender_bytes = AsyncWeb3.to_bytes(hexstr=sender)
    nonce_bytes = AsyncWeb3.to_bytes(nonce)
    rlp_encoded = encode([sender_bytes, nonce_bytes])
    contract_address = keccak(rlp_encoded)[12:]
    return AsyncWeb3.to_checksum_address(contract_address.hex())


def format_hex_string(value: str) -> str:
    hex_value = value.encode("ascii").hex()
    hex_length = hex(len(value))[2:]
    return hex_length.zfill(2) + hex_value


def generate_calldata() -> str:
    name = generate_random_string()
    name_hex = format_hex_string(name)

    symbol = generate_random_string() if need_to_generate_random_symbol() else name
    symbol_hex = format_hex_string(symbol)

    calldata = PART_OF_CALL_DATA + name_hex + DEFAULT_LINE[len(name_hex):]
    calldata += symbol_hex + DEFAULT_LINE[len(symbol_hex):]

    return calldata
