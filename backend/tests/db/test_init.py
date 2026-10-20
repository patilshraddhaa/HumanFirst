from types import SimpleNamespace

import pytest
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_init_db_registers_models_without_creating_runtime_tables(
    app_modules: SimpleNamespace,
) -> None:
    await app_modules.base.init_db()

    metadata_tables = set(app_modules.base.Base.metadata.tables)
    assert {
        "users",
        "drafts",
        "sections",
        "posts",
        "comments",
        "likes",
    }.issubset(metadata_tables)

    async with app_modules.session.engine.connect() as connection:
        table_names = await connection.run_sync(
            lambda sync_connection: inspect(sync_connection).get_table_names(),
        )

    assert table_names == []


@pytest.mark.asyncio
async def test_create_and_drop_helpers_manage_test_schema(
    app_modules: SimpleNamespace,
) -> None:
    await app_modules.base.create_all_for_test()

    async with app_modules.session.engine.connect() as connection:
        created_tables = await connection.run_sync(
            lambda sync_connection: inspect(sync_connection).get_table_names(),
        )

    assert {
        "users",
        "drafts",
        "sections",
        "posts",
        "comments",
        "likes",
    }.issubset(set(created_tables))

    await app_modules.base.drop_all_for_test()

    async with app_modules.session.engine.connect() as connection:
        remaining_tables = await connection.run_sync(
            lambda sync_connection: inspect(sync_connection).get_table_names(),
        )

    assert remaining_tables == []
