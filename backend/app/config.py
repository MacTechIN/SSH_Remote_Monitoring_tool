from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.app.models import HostConfig

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HOSTS_FILE = PROJECT_ROOT / "config" / "hosts.yaml"
EXAMPLE_HOSTS_FILE = PROJECT_ROOT / "config" / "hosts.example.yaml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    hosts_file: Path = Field(default=DEFAULT_HOSTS_FILE, alias="HOSTS_FILE")
    ssh_private_key_path: Path | None = Field(default=None, alias="SSH_PRIVATE_KEY_PATH")
    ssh_connect_timeout: float = Field(default=10.0, alias="SSH_CONNECT_TIMEOUT")
    command_timeout: float = Field(default=15.0, alias="SSH_COMMAND_TIMEOUT")
    demo_mode: bool = Field(default=False, alias="DEMO_MODE")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_hosts(settings: Settings | None = None) -> list[HostConfig]:
    settings = settings or get_settings()
    path = settings.hosts_file
    if not path.is_file():
        if EXAMPLE_HOSTS_FILE.is_file():
            path = EXAMPLE_HOSTS_FILE
        else:
            return []

    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    hosts_raw = raw.get("hosts") or []
    return [HostConfig.model_validate(item) for item in hosts_raw]


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
