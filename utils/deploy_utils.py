from typing import Tuple, Dict
from solcx import compile_standard, install_solc, get_installed_solc_versions

from constants import MAIN_CONTRACT_PATH, INTERFACE_DIR, SOLC_VERSION



def read_sol_files() -> Tuple[str, Dict[str, Dict[str, str]]]:
    with open(MAIN_CONTRACT_PATH, "r") as file:
        main_contract_code = file.read()


    dependencies = {}
    for HELLO_WORLD_FILE in INTERFACE_DIR.iterdir():
        if HELLO_WORLD_FILE.suffix == ".sol":
            with open(HELLO_WORLD_FILE, "r") as dep_file:
                dependencies[f"{HELLO_WORLD_FILE.name}"] = {
                    "content": dep_file.read()
                }


    return main_contract_code, dependencies


def ensure_solc_installed():
    installed_versions = get_installed_solc_versions()
    if SOLC_VERSION not in installed_versions:
        install_solc(SOLC_VERSION)


def compile_contracts(main_contract_code: str, dependencies: dict) -> dict:
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {
                "HelloWorld.sol": {"content": main_contract_code},
                **dependencies,
            },
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": [
                            "abi",
                            "metadata",
                            "evm.bytecode",
                            "evm.bytecode.sourceMap",
                        ]
                    }
                },
            },
        },
        solc_version=SOLC_VERSION,
    )
    return compiled_sol
