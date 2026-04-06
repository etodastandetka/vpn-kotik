from collections.abc import AsyncGenerator

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


class Base(DeclarativeBase):
    pass


# Таймаут подключения (сек.), иначе при выключенной БД /start «висит» без ответа
engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"timeout": 12},
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
