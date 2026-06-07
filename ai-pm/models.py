import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, LargeBinary
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from database import Base


def _uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")          # user | admin
    created_at = Column(DateTime, default=datetime.utcnow)
    # Fernet-encrypted JSON of this user's LLM settings (provider, keys, models).
    # Never stored in plaintext. See crypto.py.
    llm_settings_enc = Column(Text, nullable=True)
    # Fernet-encrypted JSON of this user's Jira connection (site URL, email,
    # API token, selected project key, story-points field id). Same at-rest
    # protection as llm_settings_enc. See crypto.py and services/jira_service.py.
    jira_settings_enc = Column(Text, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)


class FileBlob(Base):
    """File contents stored directly in the database (STORAGE_BACKEND=db).

    Avoids needing object storage (S3/R2) for the hosted deployment — uploads
    are small (transcripts KBs, decks a few MB) and fit comfortably in a row."""
    __tablename__ = "file_blobs"

    path = Column(String, primary_key=True)        # synthetic key returned by save()
    project_id = Column(String, index=True, nullable=True)
    content = Column(LargeBinary, nullable=False)   # BYTEA on Postgres, BLOB on SQLite
    created_at = Column(DateTime, default=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=_uuid)
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="idle")  # idle | running | awaiting_approval | complete | failed

    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    pipeline_runs = relationship("PipelineRun", back_populates="project", cascade="all, delete-orphan")
    generated_outputs = relationship("GeneratedOutput", back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # transcript | docx | pdf | pptx | image
    storage_path = Column(String, nullable=False)
    cleaned_text = Column(Text, nullable=True)  # cached cleaned content; reused across runs
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="documents")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=True)              # requirement title / PRD name
    requirement_details = Column(Text, nullable=True)  # instructions: what to build + PRD type
    persona_override = Column(String, nullable=True)
    output_style = Column(String, nullable=True)       # Plain English | Technical | Concise | Detailed
    document_ids = Column(JSON, default=list)          # documents this run used
    method = Column(String, default="AI")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    current_stage = Column(String, default="pending")
    stage_statuses = Column(JSON, default=lambda: {
        "ingestion": "pending",
        "framework": "pending",
        "checkpoint": "pending",
        "prd": "pending",
        "bdd": "pending",
        "jira_format": "pending",
    })
    approval_status = Column(String, default="not_required")  # not_required | pending | approved | rejected
    approval_notes = Column(Text, nullable=True)
    error = Column(Text, nullable=True)

    project = relationship("Project", back_populates="pipeline_runs")
    generated_outputs = relationship("GeneratedOutput", back_populates="run", cascade="all, delete-orphan")


class GeneratedOutput(Base):
    __tablename__ = "generated_outputs"

    id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(String, ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String, nullable=False)  # ingestion | framework | prd | bdd | jira_format
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="generated_outputs")
    run = relationship("PipelineRun", back_populates="generated_outputs")
