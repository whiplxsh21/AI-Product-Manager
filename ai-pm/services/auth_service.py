"""User accounts, authentication, password reset, and per-user LLM settings.

Passwords are hashed with bcrypt (never stored in plaintext). Per-user LLM
settings (provider/keys/models) are encrypted at rest via crypto.py.
"""
import secrets
from datetime import datetime, timedelta

import bcrypt

from config import config
from crypto import decrypt_json, encrypt_json
from database import SessionLocal
from models import User

RESET_TOKEN_TTL = timedelta(hours=1)


# ── Password hashing ────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ── Lookups ─────────────────────────────────────────────────────────────────

def get_user(user_id: str) -> User | None:
    db = SessionLocal()
    try:
        return db.query(User).filter_by(id=user_id).first()
    finally:
        db.close()


def get_user_by_login(identifier: str) -> User | None:
    """Look up by username or email (case-insensitive on email)."""
    db = SessionLocal()
    try:
        ident = identifier.strip()
        return (
            db.query(User)
            .filter((User.username == ident) | (User.email == ident.lower()))
            .first()
        )
    finally:
        db.close()


# ── Account management ──────────────────────────────────────────────────────

def create_user(username: str, email: str, password: str, role: str = "user") -> User:
    db = SessionLocal()
    try:
        user = User(
            username=username.strip(),
            email=email.strip().lower(),
            password_hash=hash_password(password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def register_user(username: str, email: str, password: str) -> tuple[User | None, str | None]:
    """Self-service signup. Returns (user, None) on success or (None, error)."""
    username = username.strip()
    email = email.strip().lower()
    db = SessionLocal()
    try:
        existing = (
            db.query(User)
            .filter((User.username == username) | (User.email == email))
            .first()
        )
        if existing:
            return None, "That username or email is already registered."
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, None
    except Exception:
        db.rollback()
        return None, "Could not create that account. Try a different username or email."
    finally:
        db.close()


def authenticate(identifier: str, password: str) -> User | None:
    user = get_user_by_login(identifier)
    if user and verify_password(password, user.password_hash):
        return user
    return None


def set_password(user_id: str, new_password: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if user:
            user.password_hash = hash_password(new_password)
            user.reset_token = None
            user.reset_token_expires = None
            db.commit()
    finally:
        db.close()


def seed_admin() -> None:
    """Create the configured admin account on startup if it does not exist yet.
    Idempotent — safe to call on every boot."""
    if not (config.seed_admin_username and config.seed_admin_email
            and config.seed_admin_password):
        return
    if get_user_by_login(config.seed_admin_username):
        return
    create_user(
        config.seed_admin_username,
        config.seed_admin_email,
        config.seed_admin_password,
        role="admin",
    )


# ── Password reset ──────────────────────────────────────────────────────────

def create_reset_token(email: str) -> tuple[User, str] | None:
    """Generate a time-limited reset token for the account with this email.
    Returns (user, token) or None if no such account exists."""
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email.strip().lower()).first()
        if not user:
            return None
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + RESET_TOKEN_TTL
        db.commit()
        db.refresh(user)
        return user, token
    finally:
        db.close()


def reset_password_with_token(token: str, new_password: str) -> bool:
    """Consume a reset token and set a new password. Returns False if the token
    is unknown or expired."""
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(reset_token=token).first()
        if not user or not user.reset_token_expires:
            return False
        if datetime.utcnow() > user.reset_token_expires:
            return False
        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        return True
    finally:
        db.close()


# ── Per-user LLM settings (encrypted) ─────────────────────────────────────────

def get_llm_settings(user_id: str) -> dict:
    user = get_user(user_id)
    if not user:
        return {}
    return decrypt_json(user.llm_settings_enc)


def save_llm_settings(user_id: str, settings: dict) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if user:
            user.llm_settings_enc = encrypt_json(settings)
            db.commit()
    finally:
        db.close()
