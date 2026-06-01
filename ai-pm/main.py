import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from config import config
from database import create_tables
from schemas import (
    ApprovalRequest,
    ProjectCreate,
    ProjectRead,
    DocumentRead,
    PipelineRunRead,
    GeneratedOutputRead,
    RejectRequest,
    RunRequest,
)
import services.project_service as svc


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="PM Pilot API", lifespan=lifespan)


# ── Projects ──────────────────────────────────────────────────────────────────

@app.post("/projects", response_model=ProjectRead, status_code=201)
def create_project(body: ProjectCreate):
    project = svc.create_project(body.name, body.description)
    return ProjectRead.model_validate(project)


@app.get("/projects", response_model=list[ProjectRead])
def list_projects():
    return [ProjectRead.model_validate(p) for p in svc.get_all_projects()]


@app.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: str):
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRead.model_validate(project)


@app.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str):
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    svc.delete_project(project_id)


# ── Documents ─────────────────────────────────────────────────────────────────

@app.post("/projects/{project_id}/documents", response_model=DocumentRead, status_code=201)
async def upload_document(project_id: str, file: UploadFile = File(...)):
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    content = await file.read()
    doc = svc.save_document(project_id, file.filename, content)
    return DocumentRead.model_validate(doc)


@app.get("/projects/{project_id}/documents", response_model=list[DocumentRead])
def list_documents(project_id: str):
    return [DocumentRead.model_validate(d) for d in svc.get_documents(project_id)]


@app.delete("/projects/{project_id}/documents/{document_id}", status_code=204)
def delete_document(project_id: str, document_id: str):
    svc.delete_document(document_id)


# ── Pipeline ──────────────────────────────────────────────────────────────────

@app.post("/projects/{project_id}/run", status_code=202)
def trigger_pipeline(project_id: str, body: RunRequest = RunRequest()):
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    docs = svc.get_documents(project_id)
    if not docs:
        raise HTTPException(status_code=400, detail="No documents uploaded")

    def _run():
        svc.run_pipeline(
            project_id,
            title=body.title,
            requirement_details=body.requirement_details,
            persona_override=body.persona_override,
            output_style=body.output_style,
            document_ids=body.document_ids,
        )

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=0.1)

    return {"message": "Pipeline started", "project_id": project_id}


@app.get("/projects/{project_id}/runs", response_model=list[PipelineRunRead])
def list_runs(project_id: str):
    return [PipelineRunRead.model_validate(r) for r in svc.get_runs(project_id)]


@app.get("/projects/{project_id}/runs/{run_id}/status", response_model=PipelineRunRead)
def get_run_status(project_id: str, run_id: str):
    run = svc.get_run_status(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return PipelineRunRead.model_validate(run)


@app.get("/projects/{project_id}/outputs/{stage}", response_model=GeneratedOutputRead)
def get_output(project_id: str, stage: str, run_id: str):
    output = svc.get_output(project_id, run_id, stage)
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    return GeneratedOutputRead.model_validate(output)


# ── HITL (V2 — gated) ─────────────────────────────────────────────────────────

@app.post("/projects/{project_id}/runs/{run_id}/approve", status_code=200)
def approve_run(project_id: str, run_id: str, body: ApprovalRequest):
    if not config.hitl_enabled:
        raise HTTPException(status_code=400, detail="HITL is not enabled")
    svc.approve_run(run_id, body.notes, body.edited_framework)
    return {"message": "Run approved"}


@app.post("/projects/{project_id}/runs/{run_id}/reject", status_code=200)
def reject_run(project_id: str, run_id: str, body: RejectRequest):
    if not config.hitl_enabled:
        raise HTTPException(status_code=400, detail="HITL is not enabled")
    svc.reject_run(run_id, body.notes)
    return {"message": "Run rejected"}
