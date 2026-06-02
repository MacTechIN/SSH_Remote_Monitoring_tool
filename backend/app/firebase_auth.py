from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth

from backend.app.config import get_settings

_bearer = HTTPBearer(auto_error=False)


def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict | None:
    settings = get_settings()
    if not settings.firebase_auth_required:
        return None
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
        )
    try:
        return auth.verify_id_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc
