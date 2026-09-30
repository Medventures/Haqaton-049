from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.paths import REPO_ROOT


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "sqlite:///./aqylroute.db"

    jwt_secret: str = "dev-secret-not-for-production-change-me-please"
    jwt_algorithm: str = "HS256"
    jwt_ttl_hours: int = 24 * 14

    openai_api_key: str = ""
    openai_model: str = ""

    mail_mode: str = "console"
    smtp_host: str = ""
    smtp_port: str = ""
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    demo_mode: bool = False
    demo_password: str = ""

    api_url: str = "http://localhost:8000"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
