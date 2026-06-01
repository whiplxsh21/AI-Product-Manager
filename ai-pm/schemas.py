from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    status: str


class DocumentCreate(BaseModel):
    project_id: str
    filename: str
    file_type: str
    storage_path: str


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    filename: str
    file_type: str
    storage_path: str
    created_at: datetime


class PipelineRunCreate(BaseModel):
    project_id: str


class RunRequest(BaseModel):
    title: Optional[str] = None
    requirement_details: Optional[str] = None
    persona_override: Optional[str] = None
    output_style: Optional[str] = None
    document_ids: Optional[list[str]] = None


class PipelineRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: Optional[str]
    requirement_details: Optional[str]
    persona_override: Optional[str]
    output_style: Optional[str]
    document_ids: Optional[list[str]]
    method: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    current_stage: str
    stage_statuses: dict
    approval_status: str
    approval_notes: Optional[str]
    error: Optional[str]


class GeneratedOutputCreate(BaseModel):
    project_id: str
    run_id: str
    stage: str
    content: str


class GeneratedOutputRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    run_id: str
    stage: str
    content: str
    created_at: datetime


class ApprovalRequest(BaseModel):
    notes: str = ""
    edited_framework: dict = {}


class RejectRequest(BaseModel):
    notes: str = ""
