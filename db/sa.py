"""
SQLAlchemy async database infrastructure.
Engine, session factory, Base class, dependency injection.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from typing import AsyncGenerator
from config.settings import DEBUG, DATABASE_URL, SQL_LOG, TZ as tz
# from datetime import date, datetime
from sqlalchemy import Date, DateTime
from dateutil import parser
import pytz

# 东八区
TZ = pytz.timezone(tz)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=SQL_LOG,
    # For SQLite: need check_same_thread=False
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class for all models."""

    # 重写 __setattr__，全局自动转换日期字符串
    def __setattr__(self, name: str, value):
        # 获取字段类型
        if name in self.__mapper__.columns:
            col_type = self.__mapper__.columns[name].type

            try:
                # 万能解析
                parsed = parser.parse(value)

                # 如果是 Date 类型 → 转 date
                if isinstance(col_type, Date):
                    value = parsed.date()

                # 如果是 DateTime 类型 → 保留 datetime
                elif isinstance(col_type, DateTime):
                    # DateTime 类型：自动转为 东八区
                    if parsed.tzinfo is None:
                        # 无时区 → 强制当作东八区
                        value = TZ.localize(parsed)
                    else:
                        # 有时区 → 转东八区
                        value = parsed.astimezone(TZ)
            except:
                # 解析失败就不处理，保持原值
                pass

        # 调用原来的赋值逻辑
        super().__setattr__(name, value)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a database session per request."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database - create all tables from Base metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose of the database engine."""
    await engine.dispose()
