from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.app.models import HostConfig

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HOSTS_FILE = PROJECT_ROOT / "config" / "hosts.yaml"
EXAMPLE_HOSTS_FILE = PROJECT_ROOT / "config" / "hosts.example.yaml"
DEFAULT_METRICS_DB = PROJECT_ROOT / "data" / "metrics.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    hosts_file: Path = Field(default=DEFAULT_HOSTS_FILE, alias="HOSTS_FILE")
    metrics_db_path: Path = Field(default=DEFAULT_METRICS_DB, alias="METRICS_DB_PATH")
    history_enabled: bool = Field(default=True, alias="HISTORY_ENABLED")
    ssh_private_key_path: Path | None = Field(default=None, alias="SSH_PRIVATE_KEY_PATH")
    ssh_private_key: str | None = Field(default=None, alias="SSH_PRIVATE_KEY")
    ssh_connect_timeout: float = Field(default=10.0, alias="SSH_CONNECT_TIMEOUT")
    command_timeout: float = Field(default=15.0, alias="SSH_COMMAND_TIMEOUT")
    storage_backend: str = Field(default="file", alias="STORAGE_BACKEND")
    firebase_project_id: str | None = Field(default=None, alias="FIREBASE_PROJECT_ID")
    firebase_auth_required: bool = Field(default=False, alias="FIREBASE_AUTH_REQUIRED")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    demo_mode: bool = Field(default=False, alias="DEMO_MODE")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_hosts(settings: Settings | None = None) -> list[HostConfig]:
    from backend.app.host_store import load_hosts as store_load_hosts

    return store_load_hosts(settings)


def resolve_private_key_path(host: HostConfig, settings: Settings) -> Path | None:
    if host.private_key_path:
        return Path(host.private_key_path).expanduser()
    if settings.ssh_private_key_path:
        return settings.ssh_private_key_path.expanduser()
    for candidate in (Path("~/.ssh/id_ed25519"), Path("~/.ssh/id_rsa")):
        path = candidate.expanduser()
        if path.is_file():
            return path
    return None
