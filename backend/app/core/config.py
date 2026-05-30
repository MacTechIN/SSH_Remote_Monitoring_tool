from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SSH Monitor API"
    debug: bool = False
    database_url: str = "postgresql+psycopg2://monitor:monitor@localhost:5432/monitor"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000"

    encryption_key: str = "change-me-use-fernet-key-base64"
    jwt_secret: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    admin_username: str = "admin"
    admin_password: str = "admin"

    ssh_max_concurrent: int = 10
    ssh_command_timeout: int = 30
    default_poll_interval_sec: int = 60

    min_user_uid: int = 1000

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
