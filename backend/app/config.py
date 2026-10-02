from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Loot Wallet"
    environment: str = "development"

    # SQLite keeps a fresh local checkout runnable without a separate database.
    # Set DATABASE_URL to PostgreSQL for shared or production environments.
    database_url: str = "sqlite:///./loot.db"
    # Authentication
    jwt_secret: str = "change-me-in-production-use-a-real-secret"
    access_token_expire_minutes: int = 1440  # 24 hours

    # CORS — comma-separated origins allowed to call the API.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,capacitor://localhost"

    # AI / LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # When True, FastAPI auto-creates tables on startup (local dev convenience).
    # For team/production use, set False and manage schema via `alembic upgrade`.
    create_tables_on_startup: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
