from sqlalchemy.orm import DeclarativeBase

from app.db.session import check_db_connection, engine


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    # Import models here so they register with Base.metadata before create_all.
    from app.db import models  # noqa: F401

    await check_db_connection()


async def create_all_for_test() -> None:
    from app.db import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_for_test() -> None:
    from app.db import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
