import asyncio
import aiosqlite
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import inspect
from contextlib import asynccontextmanager
from typing import Any, Optional, Dict
from datetime import datetime

from utils.request_utils import generate_random_impersonation
from db.models.base_model import Base


class DatabaseClient:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=False, future=True)
        self.async_session = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                raise e

    async def init_db(self) -> None:
        async with self.engine.begin() as conn:
            def get_table_names(connection):
                inspector = inspect(connection)
                return inspector.get_table_names()

            existing_tables = await conn.run_sync(get_table_names)

            if not existing_tables:
                await conn.run_sync(Base.metadata.create_all)
            else:
                pass

    async def add_account(
            self, model, private_key: str, proxy_url: str, session, **additional_fields
    ):
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key

        if len(private_key) != 66:
            raise

        if not proxy_url.startswith("http"):
            proxy_url = "http://" + proxy_url

        os_header, chrome_version  = generate_random_impersonation()
        
        data = {
            "time": datetime.now(),
            "private_key": private_key,
            "proxy": proxy_url,
            "deploy_contract": 0,
            "deploy_tokens": 0,
            "transfer_tokens": 0,
            "swap":0,
            "transaction_count": 0,
            "os_header": os_header.to_str(),
            "chrome_version": chrome_version.to_str(),
            "errors": "",
            **additional_fields,
        }

        check_exists = {"private_key": private_key}

        query = select(model).filter_by(**check_exists)
        result = await session.execute(query)
        exists = result.scalar_one_or_none()

        if exists:
            return False

        record = model(**data)
        session.add(record)
        return True

    async def completion_db_entry(
            self,
            model,
            data: Dict[str, Any],
            session: AsyncSession,
            check_exists: Optional[Dict[str, Any]] = None
    ) -> bool:
        try:
            if check_exists:
                query = select(model).filter_by(**check_exists)
                result = await session.execute(query)
                exists = result.scalar_one_or_none()
                if exists:

                    return False

            record = model(**data)
            session.add(record)

            return True
        except Exception as e:
            raise e

async def update_db(
            db: aiosqlite.Connection,
            table: str,
            filter_conditions: Dict[str, Any],
            update_fields: Dict[str, Any]
    ) -> None:
        """
        Обновляет данные в таблице.

        :param db: Соединение с базой данных.
        :param table: Имя таблицы.
        :param filter_conditions: Условия для фильтрации записей (например, {"id": 1}).
        :param update_fields: Поля и их новые значения для обновления (например, {"age": 31}).
        """
        try:
            set_clause = ', '.join([f"{key} = ?" for key in update_fields.keys()])
            where_clause = ' AND '.join([f"{key} = ?" for key in filter_conditions.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

            values = tuple(update_fields.values()) + tuple(filter_conditions.values())

            await db.execute(query, values)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e
