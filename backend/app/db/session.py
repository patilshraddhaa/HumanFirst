from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _engine_kwargs(database_url: str) -> dict[str, object]:
    engine_kwargs: dict[str, object] = {
        "echo": settings.database_echo,
        "future": True,
    }

    if database_url.startswith("sqlite"):
        return engine_kwargs

    engine_kwargs.update(
        pool_pre_ping=settings.database_pool_pre_ping,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )
    return engine_kwargs


engine = create_async_engine(settings.database_url, **_engine_kwargs(settings.database_url))

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


async def check_db_connection() -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
