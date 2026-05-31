from __future__ import annotations

import os

import firebase_admin
from firebase_admin import credentials, firestore

_app: firebase_admin.App | None = None
_db: firestore.Client | None = None


def get_firestore_client() -> firestore.Client:
    global _app, _db
    if _db is not None:
        return _db

    if not firebase_admin._apps:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.isfile(cred_path):
            cred = credentials.Certificate(cred_path)
            _app = firebase_admin.initialize_app(cred)
        else:
            _app = firebase_admin.initialize_app()

    _db = firestore.client()
    return _db
