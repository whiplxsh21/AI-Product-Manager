"""Platform-owned LLM configuration: API keys + Free/Pro tier definitions.

In the SaaS model the platform (not each user) owns the LLM keys. Admin defines
two tiers — `free` and `pro` — each a full LLM config (provider/model/fallback/
vision/ingestion/cleaning). At generation time a user picks a mode they're
entitled to (by their plan), and `resolve_mode()` produces the override dict the
pipeline already understands via runtime.effective_config().

Stored as a single Fernet-encrypted JSON blob (it holds API keys). Singleton row
in the platform_settings table.
"""
from __future__ import annotations

from crypto import decrypt_json, encrypt_json
from database import SessionLocal
from models import PlatformSettings

SINGLETON_ID = "platform"

# Secret keys shared by all tiers (the platform's provider credentials).
KEY_FIELDS = (
    "groq_api_key", "openai_api_key", "anthropic_api_key", "gemini_api_key",
    "openai_project",
)

# Per-tier LLM config fields. These mirror runtime.LLM_FIELDS so a tier dict can
# be handed straight to set_llm_override(); any field left blank falls through to
# the global .env config (e.g. a Groq key configured in deploy secrets).
TIER_FIELDS = (
    "paid", "paid_model",
    "llm_provider", "llm_model",
    "llm_fallback_provider", "llm_fallback_model",
    "vision_provider", "vision_model",
    "ingestion_provider", "ingestion_model",
    "cleaning_mode",
)

# Sensible defaults so the app works before an admin configures anything:
# Free = Groq (free models), Pro = paid OpenAI path.
DEFAULT_FREE = {
    "paid": False,
    "paid_model": "",
    "llm_provider": "groq",
    "llm_model": "",
    "llm_fallback_provider": "",
    "llm_fallback_model": "",
    "vision_provider": "",
    "vision_model": "",
    "ingestion_provider": "",
    "ingestion_model": "",
    "cleaning_mode": "local",
}
DEFAULT_PRO = {
    "paid": True,
    "paid_model": "gpt-5.4-mini",
    "llm_provider": "openai",
    "llm_model": "",
    "llm_fallback_provider": "",
    "llm_fallback_model": "",
    "vision_provider": "",
    "vision_model": "",
    "ingestion_provider": "",
    "ingestion_model": "",
    "cleaning_mode": "llm",
}


def _empty_keys() -> dict:
    return {k: "" for k in KEY_FIELDS}


def _merge_tier(defaults: dict, saved: dict | None) -> dict:
    out = dict(defaults)
    for k in TIER_FIELDS:
        if saved and k in saved and saved[k] not in (None,):
            out[k] = saved[k]
    return out


def get_config() -> dict:
    """Return {"keys": {...}, "free": {...}, "pro": {...}} with defaults applied.
    Secrets are decrypted; callers must not log this."""
    db = SessionLocal()
    try:
        row = db.query(PlatformSettings).filter_by(id=SINGLETON_ID).first()
        raw = decrypt_json(row.data_enc) if row and row.data_enc else {}
    finally:
        db.close()
    keys = _empty_keys()
    keys.update({k: v for k, v in (raw.get("keys") or {}).items() if k in KEY_FIELDS})
    return {
        "keys": keys,
        "free": _merge_tier(DEFAULT_FREE, raw.get("free")),
        "pro": _merge_tier(DEFAULT_PRO, raw.get("pro")),
    }


def save_config(keys: dict, free: dict, pro: dict) -> None:
    """Persist platform keys + tier definitions (encrypted). Pass the full dicts;
    blank secrets are the caller's responsibility (the UI keeps saved values)."""
    blob = {
        "keys": {k: (keys.get(k) or "") for k in KEY_FIELDS},
        "free": {k: free.get(k, DEFAULT_FREE[k]) for k in TIER_FIELDS},
        "pro": {k: pro.get(k, DEFAULT_PRO[k]) for k in TIER_FIELDS},
    }
    db = SessionLocal()
    try:
        row = db.query(PlatformSettings).filter_by(id=SINGLETON_ID).first()
        if not row:
            row = PlatformSettings(id=SINGLETON_ID)
            db.add(row)
        row.data_enc = encrypt_json(blob)
        db.commit()
    finally:
        db.close()


def resolve_mode(mode: str) -> dict:
    """Build the LLM override dict for a generation mode (free | pro): the tier's
    config merged with the platform API keys. Blank fields fall through to the
    global .env config in runtime.effective_config()."""
    cfg = get_config()
    tier = cfg["pro"] if mode == "pro" else cfg["free"]
    override = dict(tier)
    override.update(cfg["keys"])
    return override


def allowed_modes(plan: str | None) -> list[str]:
    """Modes a user may use. Pro can use both; everyone else gets Free."""
    return ["free", "pro"] if plan == "pro" else ["free"]
