from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Local dev default uses SQLite so the app runs without a Postgres install.
    # Production (RSERVER) sets DATABASE_URL to a postgresql+psycopg2:// URL via .env.
    database_url: str = "sqlite:///./dev.db"


settings = Settings()
