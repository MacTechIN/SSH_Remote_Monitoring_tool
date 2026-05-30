import os
from functools import lru_cache
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parent / ".env"


def _load_dotenv() -> None:
    if not _ENV_FILE.exists():
        return
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


_load_dotenv()


@lru_cache
def firebase_settings() -> dict:
    return {
        "encryption_key": os.environ.get("ENCRYPTION_KEY", ""),
        "jwt_secret": os.environ.get("JWT_SECRET", "firebase-change-me"),
        "admin_username": os.environ.get("ADMIN_USERNAME", "admin"),
        "admin_password": os.environ.get("ADMIN_PASSWORD", "admin"),
        "cors_origins": os.environ.get("CORS_ORIGINS", "*"),
    }


def apply_to_backend_settings() -> None:
    """Map Firebase secrets/env to backend pydantic Settings."""
    s = firebase_settings()
    os.environ.setdefault("ENCRYPTION_KEY", s["encryption_key"])
    os.environ.setdefault("JWT_SECRET", s["jwt_secret"])
    os.environ.setdefault("ADMIN_USERNAME", s["admin_username"])
    os.environ.setdefault("ADMIN_PASSWORD", s["admin_password"])
