from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:5173"]
    cors_allow_credentials: bool = True
    debug: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/humanfirst"
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_pre_ping: bool = True
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_ttl_minutes: int = 60
    mcp_token_prefix: str = "hf_"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001
    mcp_public_path: str = "/mcp"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
