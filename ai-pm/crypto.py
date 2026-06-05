"""Symmetric encryption for secrets stored at rest (per-user LLM API keys).

A Fernet key is derived from APP_SECRET_KEY so the operator can supply any
random string rather than a precisely-formatted Fernet key. The master key
lives only in the app environment (Streamlit secrets), never in the database:
so a database leak alone does not expose usable API keys.

Note: if APP_SECRET_KEY changes, previously-encrypted values become
unreadable and decrypt_json() returns {} (users simply re-enter their keys).
"""
import base64
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken
from config import config


def _fernet() -> Fernet:
    secret = config.app_secret_key or "dev-insecure-key-change-me"
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def encrypt_json(data: dict) -> str:
    return _fernet().encrypt(json.dumps(data).encode("utf-8")).decode("utf-8")


def decrypt_json(token: str | None) -> dict:
    if not token:
        return {}
    try:
        return json.loads(_fernet().decrypt(token.encode("utf-8")).decode("utf-8"))
    except (InvalidToken, ValueError):
        return {}
