from concurrent.futures import ProcessPoolExecutor
import asyncio
import random
from multiprocessing import Process, Manager
from asyncio import WindowsSelectorEventLoopPolicy
from sqlalchemy.future import select
from datetime import datetime, timedelta

from db.models.rome_model import RomeLabs
from src.captcha_solver import CaptchaSolver
from src.rome_labs_client import RomeLabsClient
from utils.deploy_utils import read_sol_files, ensure_solc_installed, compile_contracts
from utils.file_utils import read_lines
from utils.request_utils import Impersonate, ImpersonateOs
from utils.broker_utils import TaskExecutor
from config import RANDOM_SLEEP_DELAY, CAPTCHA_API_KEY, MAX_CONCURRENT_TASKS, DB_PATH, NUMBER_OF_WAITING_DAYS
from constants import RPC_URL, EXPLORER_URL
from db.db_client import DatabaseClient, update_db


DB_CLIENT = DatabaseClient(DB_PATH)

MAIN_CONTRACT_CODE, DEPENDENCIES = read_sol_files()
COMPILED_CONTRACT = compile_contracts(MAIN_CONTRACT_CODE, DEPENDENCIES)
ensure_solc_installed()


def start_process_wallet(wallet, broker, mask_id):
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    return asyncio.run(process_wallet(wallet, broker, mask_id))


async def process_wallet(wallet, broker, mask_id=False):


    pk = wallet.private_key
    proxy_url = wallet.proxy
    wallet_id = wallet.id
    displayed_id = "***" if mask_id else str(wallet_id)
    os_data = wallet.os_header
    chrome_version = wallet.chrome_version

    if not pk.startswith("0x"):
        pk = "0x" + pk

    if len(pk) != 66:
        raise

    if not proxy_url.startswith("http"):
        proxy_url = "http://" + proxy_url

    os: ImpersonateOs = ImpersonateOs.from_str(os_data)
    version: Impersonate = Impersonate.from_str(chrome_version)

    headers = version.headers(os)

    client = RomeLabsClient(
        rpc_url=RPC_URL,
        private_key=pk,
        explorer_url=EXPLORER_URL,
        proxy_url=proxy_url,
        logger_id=displayed_id,
        retry_attempts=3,
        timeout_429=60,
        headers=headers
    )

    logger = client.logger

    try:
        logger.info(f"Начинаем работу...")

        random_delay = random.uniform(*RANDOM_SLEEP_DELAY)
        await asyncio.sleep(random_delay)

        print(random_delay)

        s = CaptchaSolver(api_key=CAPTCHA_API_KEY, proxy_url=proxy_url, headers=headers)
        print(s)
        task_id = await s.create_task_for_captcha()
        print(task_id)
        captcha_key = await s.get_captcha_key(task_id)
        print(captcha_key)
        await client.send_airdrop_request(amount="100", captcha_response=captcha_key)

        random_delay = random.uniform(*RANDOM_SLEEP_DELAY)
        print(random_delay)
        await asyncio.sleep(random_delay)


        print(1)

        try:
            tx_count = await client.web3_account.get_transaction_counts()
            broker.enqueue_task(update_db, "RomeLabs",
                                {"private_key": pk}, {"transaction_count": tx_count})
        except Exception as e:
            logger.error(f"Ошибка при записи транзакций в базу: {e}")


        try:
            if await client.deploy_hello_world_contract(COMPILED_CONTRACT):
                broker.enqueue_task(update_db, "RomeLabs",
                                    {"private_key": pk}, {"deploy_contract": 1}
                                    )
        except Exception as e:
            logger.error(f"Ошибка при развертывании HelloWorld контракта: {e}")


        try:
            if client.deploy_own_tokens():
                broker.enqueue_task(update_db, "RomeLabs",
                                    {"private_key": pk}, {"deploy_tokens": wallet.deploy_tokens + 1}
                                    )
        except Exception as e:
            logger.error(f"Ошибка при развертывании токенов: {e}")


        try:
            if await client.prepare_transfer_tx():
                broker.enqueue_task(update_db, "RomeLabs",
                                    {"private_key": pk}, {"transfer_tokens": wallet.transfer_tokens + 1}
                                    )
        except Exception as e:
            logger.error(f"Ошибка при передаче токенов: {e}")


        try:
            if await client.swap():
                broker.enqueue_task(update_db, "RomeLabs",
                                    {"private_key": pk}, {"swap": wallet.swap + 1}
                                    )

        except Exception as e:
            logger.error(f"Ошибка при передаче токенов: {e}")

        broker.enqueue_task(update_db, "RomeLabs",
                            {"private_key": pk}, {"time": datetime.now()}
                            )


        logger.info(f"[ID: {displayed_id}] Все задачи завершены.\n")
    except Exception as e:
        logger.error(f"Общая ошибка: {e}")


async def main():
    print("Выберите действие:")
    print("1: Заполнить данные в базу")
    print("2: Запустить активности (показывать ID)")
    print("3: Запустить активности (скрыть ID)")

    choice = input("Введите номер действия: ")

    if choice == "1":
        await DB_CLIENT.init_db()

        private_keys = read_lines("./data/private_keys.txt")
        proxies = read_lines("./data/proxies.txt")

        if len(private_keys) != len(proxies):
            return

        async with DB_CLIENT.get_session() as session:
            for pk, proxy in zip(private_keys, proxies):
                await DB_CLIENT.add_account(RomeLabs, pk, proxy, session)
    elif choice in ("2", "3"):
        try:
            await DB_CLIENT.init_db()
            mask_id = choice == "3"

            async with DB_CLIENT.get_session() as session:
                rows = await session.execute(select(RomeLabs))
                wallets = rows.scalars().all()

            manager = Manager()
            shared_queue = manager.Queue()
            broker = TaskExecutor(shared_queue)
            process = Process(target=broker.run_async_tasks)
            process.start()

            with ProcessPoolExecutor(max_workers=MAX_CONCURRENT_TASKS) as executor:
                futures = []
                for wallet in wallets:

                    # time_condition = datetime.now() > wallet.time + timedelta(days=NUMBER_OF_WAITING_DAYS)
                    #
                    # if time_condition:

                    future = executor.submit(start_process_wallet, wallet, broker, mask_id)
                    futures.append(future)

                for future in futures:
                    future.result()

            broker.close(process)
            print("Все процессы завершены")
        except Exception as e:
            raise e


if __name__ == "__main__":
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main())