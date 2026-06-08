"""Async SQLAlchemy infrastructure for the external demo database.

This database is managed by reverse-engineered models. Do not run metadata
create/drop operations against it from the app.
"""

import os
from typing import AsyncGenerator

from sqlalchemy import Date, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from dateutil import parser
import pytz

from config.settings import BASE_DIR, SQL_LOG, TZ as tz


DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'db', 'db_external.sqlite3')}"
TZ = pytz.timezone(tz)

engine = create_async_engine(
    DATABASE_URL,
    echo=SQL_LOG,
    connect_args={"check_same_thread": False},
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    def __setattr__(self, name: str, value):
        if name in self.__mapper__.columns:
            col_type = self.__mapper__.columns[name].type
            try:
                parsed = parser.parse(value)
                if isinstance(col_type, Date):
                    value = parsed.date()
                elif isinstance(col_type, DateTime):
                    value = TZ.localize(parsed) if parsed.tzinfo is None else parsed.astimezone(TZ)
            except Exception:
                pass
        super().__setattr__(name, value)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    await engine.dispose()
