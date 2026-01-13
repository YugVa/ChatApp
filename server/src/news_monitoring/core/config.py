from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "news-monitoring"
    log_level: str = "INFO"

    postgres_dsn: str

    telegram_api_id: int | None = None
    telegram_api_hash: str | None = None
    telethon_session: str = "news_monitoring"

    bot_token: str | None = None
    bot_allowed_ids: str | None = None
    status_chat_id: str | None = None


settings = Settings()
