from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
print(BASE_DIR)


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str = "test"
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )


settings = Settings()
environment = settings.model_config
