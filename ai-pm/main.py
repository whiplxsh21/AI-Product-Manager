import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from database import create_tables
from schemas import (
    ContinueReviewRequest,
    ProjectCreate,
    ProjectRead,
    DocumentRead,
    PipelineRunRead,
    GeneratedOutputRead,
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
            prd_review=body.prd_review,
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


# ── PRD review (human-in-the-loop) ────────────────────────────────────────────

@app.post("/projects/{project_id}/runs/{run_id}/continue", status_code=202)
def continue_review(project_id: str, run_id: str,
                    body: ContinueReviewRequest = ContinueReviewRequest()):
    """Resume a PRD-review run: optionally apply an edited PRD, then generate the
    remaining deliverables (BDD, Jira, wireframe, UX flow) in the background."""
    run = svc.get_run_status(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    def _continue():
        svc.continue_after_prd_review(run_id, edited_prd=body.edited_prd)

    thread = threading.Thread(target=_continue, daemon=True)
    thread.start()
    thread.join(timeout=0.1)
    return {"message": "Generating remaining deliverables", "run_id": run_id}
