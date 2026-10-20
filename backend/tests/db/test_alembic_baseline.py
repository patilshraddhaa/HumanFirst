from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_baseline_offline_sql_emits_each_enum_type_once(
    monkeypatch,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    database_url = "postgresql+asyncpg://humanfirst:humanfirst@localhost/humanfirst"

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("DATABASE_ECHO", "false")

    sql_buffer = StringIO()
    alembic_config = Config(str(backend_root / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(backend_root / "alembic"))
    alembic_config.set_main_option("sqlalchemy.url", database_url)

    with redirect_stdout(sql_buffer):
        command.upgrade(alembic_config, "head", sql=True)

    sql = sql_buffer.getvalue()
    assert sql.count("CREATE TYPE draft_status AS ENUM") == 1
    assert sql.count("CREATE TYPE section_author_type AS ENUM") == 1
    assert sql.count("CREATE TYPE section_content_type AS ENUM") == 1
    assert sql.count("CREATE TYPE section_creation_source AS ENUM") == 1
