from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, AsyncGenerator

import pytz
from dateutil import parser
from sqlalchemy import Date, DateTime
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


def get_default_database_name() -> str:
    return next(iter(settings.DATABASES))


def normalize_database_name(database: str | None = None) -> str:
    return database or get_default_database_name()


def get_database_config(database: str | None = None) -> dict[str, Any]:
    database_name = normalize_database_name(database)
    try:
        return settings.DATABASES[database_name]
    except KeyError as exc:
        raise KeyError(f"Database[{database_name}] is not configured in settings.DATABASES.") from exc


def get_model_database(model) -> str:
    model_database = model.__dict__.get("database")
    if model_database:
        return normalize_database_name(model_database)
    base_database = getattr(model, "__database__", None)
    return normalize_database_name(base_database)


def get_model_base_app_name(model) -> str | None:
    return getattr(model, "__app_name__", None)


def infer_app_name_from_module(model) -> str | None:
    module = getattr(model, "__module__", "")
    parts = module.split(".")
    if "apps" in parts:
        app_index = parts.index("apps") + 1
        if app_index < len(parts):
            return parts[app_index]
    return None


def get_model_app_name(model) -> str:
    model_app_name = model.__dict__.get("app_name")
    if model_app_name:
        return model_app_name
    base_app_name = get_model_base_app_name(model)
    if base_app_name:
        return base_app_name
    try:
        from apps.udadmin.utils.app_registry import get_current_app_name

        current_app_name = get_current_app_name()
        if current_app_name:
            return current_app_name
    except Exception:
        pass
    module_app_name = infer_app_name_from_module(model)
    if module_app_name:
        return module_app_name
    return model.__tablename__.split("_")[0]


def _sqlite_engine_options(url: str) -> dict[str, Any]:
    if url.startswith("sqlite") and "check_same_thread" not in url:
        return {"connect_args": {"check_same_thread": False}}
    return {}


def _ensure_sqlite_parent_dir(url: str) -> None:
    parsed_url = make_url(url)
    if parsed_url.get_backend_name() != "sqlite" or not parsed_url.database:
        return
    if parsed_url.database == ":memory:":
        return
    Path(parsed_url.database).parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_engine(database: str | None = None):
    database_name = normalize_database_name(database)
    config = get_database_config(database_name)
    url = config["url"]
    engine_options = dict(_sqlite_engine_options(url))
    engine_options.update(config.get("engine_options") or {})
    return create_async_engine(url, **engine_options)


@lru_cache
def get_session_factory(database: str | None = None):
    return async_sessionmaker(
        get_engine(database),
        class_=AsyncSession,
        expire_on_commit=False,
    )


@lru_cache
def _get_database_base(database: str | None = None) -> type[DeclarativeBase]:
    database_name = normalize_database_name(database)
    timezone = pytz.timezone(getattr(settings, "TZ", "Asia/Shanghai"))

    class RegistryBase(DeclarativeBase):
        __abstract__ = True
        __database__ = database_name

        def __setattr__(self, name: str, value):
            if name in self.__mapper__.columns:
                col_type = self.__mapper__.columns[name].type
                try:
                    parsed = parser.parse(value)
                    if isinstance(col_type, Date):
                        value = parsed.date()
                    elif isinstance(col_type, DateTime):
                        value = (
                            timezone.localize(parsed)
                            if parsed.tzinfo is None
                            else parsed.astimezone(timezone)
                        )
                except Exception:
                    pass
            super().__setattr__(name, value)

    return RegistryBase


@lru_cache
def get_app_base(database: str | None = None, app_name: str | None = None) -> type[DeclarativeBase]:
    database_name = normalize_database_name(database)
    parent_base = _get_database_base(database_name)

    class RegistryAppBase(parent_base):
        __abstract__ = True
        __database__ = database_name
        __app_name__ = app_name

    return RegistryAppBase


def get_base(database: str | None = None, app_name: str | None = None) -> type[DeclarativeBase]:
    if app_name:
        return get_app_base(database, app_name)
    return _get_database_base(database)


def create_db_dependency(database: str | None = None):
    database_name = normalize_database_name(database)
    session_factory = get_session_factory(database_name)

    async def _get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    return _get_db


@lru_cache
def get_db_dependency(database: str | None = None):
    return create_db_dependency(database)


async def init_db(database: str | None = None):
    database_name = normalize_database_name(database)
    _ensure_sqlite_parent_dir(get_database_config(database_name)["url"])
    async with get_engine(database_name).begin() as conn:
        await conn.run_sync(get_base(database_name).metadata.create_all)


async def close_db(database: str | None = None):
    await get_engine(database).dispose()


async def close_all():
    for database_name in settings.DATABASES:
        await close_db(database_name)
