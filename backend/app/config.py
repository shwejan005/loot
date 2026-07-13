from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Loot"
    environment: str = "development"

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/loot"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    sync_poll_interval_seconds: int = 30
    sync_batch_size: int = 50

    # LeetCode submission history requires an authenticated session cookie.
    leetcode_session: str = ""

    # When True, FastAPI auto-creates tables on startup (local dev convenience).
    # For team/production use, set False and manage schema via `alembic upgrade`.
    create_tables_on_startup: bool = True


settings = Settings()
