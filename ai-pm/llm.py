import time

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from runtime import effective_config

_TRANSIENT_KEYWORDS = ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED",
                       "rate", "quota", "overloaded", "high demand")
# Per-minute token/request limits clear by waiting out the window, so back off
# for roughly a full minute rather than a few seconds.
_TPM_KEYWORDS = ("tokens per minute", "TPM", "rate_limit_exceeded", "413")

# Default model per role and provider.
#   main   → heavy reasoning model for framework analysis + PRD writing
#   light  → cheap, high-rate-limit model for single-pass transcript cleaning
#   vision → multimodal model for image description (kept light on purpose)
_DEFAULT_MODELS = {
    "main": {
        "groq": "llama-3.3-70b-versatile",
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20241022",
        "gemini": "gemini-2.5-flash",
        "ollama": "llama3.2",
    },
    "light": {
        "groq": "llama-3.1-8b-instant",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-20241022",
        "gemini": "gemini-2.0-flash-lite",
        "ollama": "llama3.2",
    },
    "vision": {
        "groq": "llama-3.2-11b-vision-preview",
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20241022",
        "gemini": "gemini-2.0-flash-lite",
        "ollama": "llava",
    },
}


def invoke_with_retry(llm: BaseChatModel, messages: list[BaseMessage],
                      max_attempts: int = 5) -> BaseMessage:
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return llm.invoke(messages)
        except Exception as e:
            last_exc = e
            err = str(e)
            if attempt >= max_attempts - 1:
                raise
            if any(k in err for k in _TPM_KEYWORDS):
                time.sleep(62)  # wait out the per-minute window
            elif any(k in err for k in _TRANSIENT_KEYWORDS):
                time.sleep(2 ** (attempt + 2))  # 4 → 8 → 16 → 32s
            else:
                raise
    raise last_exc


def invoke_with_fallback(llms: list[BaseChatModel], messages: list[BaseMessage]) -> BaseMessage:
    """Try each model in order. Primary models fail fast (1 attempt) so we fall
    back quickly when one is exhausted; the last model gets full retry treatment."""
    last_exc = None
    for i, llm in enumerate(llms):
        is_last = i == len(llms) - 1
        try:
            resp = invoke_with_retry(llm, messages, max_attempts=5 if is_last else 1)
            # An empty/blocked response (e.g. a thinking model exhausting its
            # output budget) is a failure too — fall back rather than return it.
            if not is_last and not (resp.content or "").strip():
                raise ValueError("empty response from primary model")
            return resp
        except Exception as e:
            last_exc = e
            if is_last:
                raise
    raise last_exc


def _build_model(provider: str, model: str, temperature: float) -> BaseChatModel:
    cfg = effective_config()
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, temperature=temperature, api_key=cfg.groq_api_key)
    elif provider == "openai":
        import os
        from langchain_openai import ChatOpenAI
        # The openai SDK reads OPENAI_PROJECT from the environment; setting it
        # here scopes paid usage to the configured project for billing.
        if cfg.openai_project:
            os.environ["OPENAI_PROJECT"] = cfg.openai_project
        return ChatOpenAI(model=model, temperature=temperature, api_key=cfg.openai_api_key)
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, temperature=temperature, api_key=cfg.anthropic_api_key)
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        # 2.5 models reserve part of the output budget for "thinking"; without a
        # generous max_output_tokens the visible content can come back empty.
        return ChatGoogleGenerativeAI(model=model, temperature=temperature,
                                      google_api_key=cfg.gemini_api_key,
                                      max_output_tokens=8192)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature)

    raise ValueError(f"Unknown LLM provider: {provider}")


def _resolve(role: str, provider: str, model: str) -> tuple[str, str]:
    provider = provider or effective_config().llm_provider
    if not model:
        defaults = _DEFAULT_MODELS[role]
        if provider not in defaults:
            raise ValueError(f"No default {role} model for provider '{provider}'")
        model = defaults[provider]
    return provider, model


PAID_MODEL = "gpt-5.4-mini"   # the only paid model used; do not introduce others


def _build_paid_model(temperature: float) -> BaseChatModel:
    return _build_model("openai", PAID_MODEL, temperature)


def get_llm(temperature: float = 0.2) -> BaseChatModel:
    cfg = effective_config()
    if cfg.paid:
        return _build_paid_model(temperature)
    provider, model = _resolve("main", cfg.llm_provider, cfg.llm_model)
    return _build_model(provider, model, temperature)


def get_main_llms(temperature: float = 0.2) -> list[BaseChatModel]:
    """In paid mode: only gpt-5.4-mini. In free mode: primary + configured
    fallback. Used with invoke_with_fallback by the framework + PRD nodes."""
    cfg = effective_config()
    if cfg.paid:
        return [_build_paid_model(temperature)]
    chain = [get_llm(temperature)]
    if cfg.llm_fallback_provider:
        provider, model = _resolve("main", cfg.llm_fallback_provider, cfg.llm_fallback_model)
        chain.append(_build_model(provider, model, temperature))
    return chain


def get_ingestion_llm(temperature: float = 0.0) -> BaseChatModel:
    cfg = effective_config()
    if cfg.paid:
        return _build_paid_model(temperature)
    provider, model = _resolve("light", cfg.ingestion_provider, cfg.ingestion_model)
    return _build_model(provider, model, temperature)


def get_vision_llm(temperature: float = 0.2) -> BaseChatModel:
    cfg = effective_config()
    if cfg.paid:
        return _build_paid_model(temperature)
    provider, model = _resolve("vision", cfg.vision_provider, cfg.vision_model)
    return _build_model(provider, model, temperature)
