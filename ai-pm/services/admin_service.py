"""Admin-only management of organizations and user accounts.

The platform admin provisions client organizations and the users inside them,
sets each user's plan (free | pro) and role (user | admin), and can reset
passwords or remove accounts. Self-service registration is disabled
(config.allow_registration defaults False) — accounts are created here.

Only the Streamlit Admin page (gated on role == "admin") calls these.
"""
from __future__ import annotations

import services.auth_service as auth
from database import SessionLocal
from models import Organization, Project, User

VALID_PLANS = ("free", "pro")
VALID_ROLES = ("user", "admin")


# ── Organizations ─────────────────────────────────────────────────────────────

def list_organizations() -> list[Organization]:
    db = SessionLocal()
    try:
        return db.query(Organization).order_by(Organization.name).all()
    finally:
        db.close()


def create_organization(name: str) -> tuple[Organization | None, str | None]:
    name = (name or "").strip()
    if not name:
        return None, "Organization name is required."
    db = SessionLocal()
    try:
        if db.query(Organization).filter(Organization.name == name).first():
            return None, "An organization with that name already exists."
        org = Organization(name=name)
        db.add(org)
        db.commit()
        db.refresh(org)
        return org, None
    except Exception:
        db.rollback()
        return None, "Could not create that organization."
    finally:
        db.close()


def org_name_map() -> dict[str, str]:
    """{org_id: name} for labelling users in the UI."""
    return {o.id: o.name for o in list_organizations()}


def user_counts_by_org() -> dict[str, int]:
    db = SessionLocal()
    try:
        rows = db.query(User.org_id).all()
        counts: dict[str, int] = {}
        for (oid,) in rows:
            if oid:
                counts[oid] = counts.get(oid, 0) + 1
        return counts
    finally:
        db.close()


# ── Users ─────────────────────────────────────────────────────────────────────

def list_users(org_id: str | None = None) -> list[User]:
    db = SessionLocal()
    try:
        q = db.query(User)
        if org_id is not None:
            q = q.filter(User.org_id == org_id)
        return q.order_by(User.created_at.desc()).all()
    finally:
        db.close()


def provision_user(username: str, email: str, password: str, *,
                   org_id: str | None, plan: str = "free",
                   role: str = "user") -> tuple[User | None, str | None]:
    """Admin-create an account. Returns (user, None) or (None, error)."""
    username = (username or "").strip()
    email = (email or "").strip().lower()
    if not username or not email:
        return None, "Username and email are required."
    if len(password or "") < 8:
        return None, "Password must be at least 8 characters."
    if plan not in VALID_PLANS:
        return None, "Invalid plan."
    if role not in VALID_ROLES:
        return None, "Invalid role."

    db = SessionLocal()
    try:
        existing = (
            db.query(User)
            .filter((User.username == username) | (User.email == email))
            .first()
        )
        if existing:
            return None, "That username or email is already registered."
    finally:
        db.close()

    user = auth.create_user(username, email, password, role=role,
                            org_id=org_id, plan=plan)
    return user, None


def set_user_plan(user_id: str, plan: str) -> None:
    if plan not in VALID_PLANS:
        raise ValueError(f"Invalid plan: {plan}")
    _update_user(user_id, plan=plan)


def set_user_role(user_id: str, role: str) -> None:
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}")
    _update_user(user_id, role=role)


def set_user_org(user_id: str, org_id: str | None) -> None:
    _update_user(user_id, org_id=org_id)


def _update_user(user_id: str, **fields) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return
        for k, v in fields.items():
            setattr(user, k, v)
        db.commit()
    finally:
        db.close()


def reset_user_password(user_id: str, new_password: str) -> None:
    """Admin sets a user's password directly (no email round-trip)."""
    auth.set_password(user_id, new_password)


def delete_user(user_id: str) -> None:
    """Remove a user. Their projects (owner_id) cascade per the FK."""
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if user:
            db.delete(user)
            db.commit()
    finally:
        db.close()


def project_count_for_user(user_id: str) -> int:
    db = SessionLocal()
    try:
        return db.query(Project).filter_by(owner_id=user_id).count()
    finally:
        db.close()
