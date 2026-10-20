import importlib
import sys

import pytest
from pydantic import ValidationError


def test_settings_require_explicit_jwt_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    sys.modules.pop("app.core.config", None)

    with pytest.raises(ValidationError) as exc_info:
        importlib.import_module("app.core.config")

    assert "jwt_secret_key" in str(exc_info.value)


def test_settings_reject_short_jwt_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "too-short")
    sys.modules.pop("app.core.config", None)

    with pytest.raises(ValidationError) as exc_info:
        importlib.import_module("app.core.config")

    assert "jwt_secret_key" in str(exc_info.value)
    assert "at least 32 characters" in str(exc_info.value)


def test_settings_default_to_postgres_runtime_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-for-config-check-1234")
    sys.modules.pop("app.core.config", None)

    config_module = importlib.import_module("app.core.config")
    settings = config_module.Settings()

    assert settings.database_url == "postgresql+asyncpg://postgres:postgres@localhost:5432/humanfirst"
    assert settings.database_echo is False
    assert settings.database_pool_size == 10
    assert settings.database_max_overflow == 20
    assert settings.database_pool_pre_ping is True
