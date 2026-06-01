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
    paid: bool = False                # True → every LLM task uses OpenAI gpt-5.4-mini
    openai_api_key: str = ""
    openai_project: str = ""          # OpenAI project ID/name for billing scope
    anthropic_api_key: str = ""
    gemini_api_key: str = ""

    # Database
    database_url: str = "sqlite:///./aipm.db"

    # Storage
    storage_backend: str = "local"
    storage_local_path: str = "./storage"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = ""
    aws_s3_region: str = ""

    # Pipeline
    hitl_enabled: bool = False

    # Jira
    jira_enabled: bool = False
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = ""


config = Settings()
