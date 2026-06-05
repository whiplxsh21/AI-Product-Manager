from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_HERE = Path(__file__).parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_HERE / ".env"), extra="ignore")

    # LLM
    llm_provider: str = "groq"
    llm_model: str = ""
    llm_fallback_provider: str = ""   # used by framework + PRD if primary is exhausted
    llm_fallback_model: str = ""
    groq_api_key: str = ""
    vision_provider: str = ""
    vision_model: str = ""
    ingestion_provider: str = ""
    ingestion_model: str = ""
    cleaning_mode: str = "local"      # local (regex, no LLM) | llm (LLM, regex fallback)
    paid: bool = False                # True → every LLM task uses OpenAI (paid_model)
    paid_model: str = ""              # OpenAI model for paid mode; blank → gpt-5.4-mini
    openai_api_key: str = ""
    openai_project: str = ""          # OpenAI project ID/name for billing scope
    anthropic_api_key: str = ""
    gemini_api_key: str = ""

    # Database
    database_url: str = "sqlite:///./aipm.db"

    # Storage
    storage_backend: str = "local"   # local | s3 | db  (db = blobs in the SQL database)
    storage_local_path: str = "./storage"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = ""
    aws_s3_region: str = ""

    # Auth / accounts
    auth_enabled: bool = False        # True → login required (hosted deploy)
    allow_registration: bool = True   # True → show the "Create account" tab on login
    app_secret_key: str = ""          # Fernet key for encrypting per-user LLM keys at rest
    app_base_url: str = ""            # public URL, used to build password-reset links
    seed_admin_username: str = ""     # optional: auto-create this admin user on startup
    seed_admin_email: str = ""
    seed_admin_password: str = ""

    # Email (password reset) — Resend
    resend_api_key: str = ""
    email_from: str = "PM Pilot <onboarding@resend.dev>"

    # Pipeline
    hitl_enabled: bool = False

    # Jira
    jira_enabled: bool = False
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = ""


config = Settings()
