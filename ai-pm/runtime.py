"""Per-request LLM configuration override.

The pipeline normally reads LLM provider/model/key settings from the global
`config` singleton (driven by .env). In the hosted multi-user app each user
supplies their own settings, so the active run must use that user's values
instead of the global ones.

A run executes synchronously inside one thread (LangGraph's `invoke`), so a
context variable set at the top of that thread is visible to every node it
calls. `effective_config()` overlays the per-run override on top of the global
config: any field the user actually set wins; anything left blank falls back to
the global default (e.g. a shared Groq key configured in deploy secrets).
"""
import contextvars

from config import config

# LLM-related fields a per-user override may set. Non-LLM config (database,
# storage, auth, …) always comes from the global config.
LLM_FIELDS = (
    "llm_provider", "llm_model", "llm_fallback_provider", "llm_fallback_model",
    "vision_provider", "vision_model", "ingestion_provider", "ingestion_model",
    "groq_api_key", "openai_api_key", "openai_project",
    "anthropic_api_key", "gemini_api_key",
    "paid", "paid_model", "cleaning_mode",
)

_override: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "llm_override", default=None
)


class _EffectiveConfig:
    """Reads overridden LLM fields first, falls back to global config."""

    def __init__(self, override: dict | None):
        self._o = override or {}

    def __getattr__(self, name):
        if name in self._o:
            val = self._o[name]
            # Blank string / None means "not configured" → use the global default.
            if val not in (None, ""):
                return val
        return getattr(config, name)


def set_llm_override(settings: dict | None) -> None:
    """Set the active per-run LLM settings (call at the top of a run thread)."""
    _override.set(settings)


def effective_config() -> _EffectiveConfig:
    return _EffectiveConfig(_override.get())
