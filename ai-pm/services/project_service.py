import uuid
from datetime import datetime

from database import SessionLocal
from models import Document, GeneratedOutput, PipelineRun, Project
from runtime import set_llm_override
from storage import get_storage

_FILE_TYPE_MAP = {
    "txt": "transcript",
    "md": "transcript",
    "docx": "docx",
    "pdf": "pdf",
    "pptx": "pptx",
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
    "webp": "image",
}


def _detect_file_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _FILE_TYPE_MAP.get(ext, "transcript")


# ── Projects ──────────────────────────────────────────────────────────────────

def create_project(name: str, description: str | None = None,
                   owner_id: str | None = None) -> Project:
    db = SessionLocal()
    try:
        project = Project(id=str(uuid.uuid4()), name=name, description=description,
                          owner_id=owner_id)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    finally:
        db.close()


def get_all_projects(owner_id: str | None = None) -> list[Project]:
    """Return projects, scoped to one owner when owner_id is given. With no
    owner_id (auth disabled / admin), returns every project."""
    db = SessionLocal()
    try:
        q = db.query(Project)
        if owner_id is not None:
            q = q.filter_by(owner_id=owner_id)
        return q.order_by(Project.created_at.desc()).all()
    finally:
        db.close()


def get_project(project_id: str) -> Project | None:
    db = SessionLocal()
    try:
        return db.query(Project).filter_by(id=project_id).first()
    finally:
        db.close()


def delete_project(project_id: str) -> None:
    db = SessionLocal()
    try:
        project = db.query(Project).filter_by(id=project_id).first()
        if project:
            db.delete(project)
            db.commit()
    finally:
        db.close()


# ── Documents ─────────────────────────────────────────────────────────────────

def save_document(project_id: str, filename: str, file_bytes: bytes,
                  file_type: str | None = None) -> Document:
    ft = file_type or _detect_file_type(filename)
    storage = get_storage()
    path = storage.save(project_id, filename, file_bytes)

    db = SessionLocal()
    try:
        doc = Document(
            id=str(uuid.uuid4()),
            project_id=project_id,
            filename=filename,
            file_type=ft,
            storage_path=path,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc
    finally:
        db.close()


def delete_document(document_id: str) -> None:
    db = SessionLocal()
    try:
        doc = db.query(Document).filter_by(id=document_id).first()
        if doc:
            get_storage().delete(doc.storage_path)
            db.delete(doc)
            db.commit()
    finally:
        db.close()


def get_documents(project_id: str) -> list[Document]:
    db = SessionLocal()
    try:
        return db.query(Document).filter_by(project_id=project_id).order_by(Document.created_at).all()
    finally:
        db.close()


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_pipeline(
    project_id: str,
    title: str | None = None,
    requirement_details: str | None = None,
    persona_override: str | None = None,
    output_style: str | None = None,
    document_ids: list[str] | None = None,
    llm_settings: dict | None = None,
) -> str:
    # Runs in a background thread; bind this user's LLM settings to this run so
    # every node uses their provider/keys/models (falls back to global config).
    set_llm_override(llm_settings)

    from pipeline.graph import compiled_graph

    run_id = str(uuid.uuid4())
    all_docs = get_documents(project_id)
    if document_ids:
        selected = [d for d in all_docs if d.id in set(document_ids)]
    else:
        selected = all_docs
    selected_ids = [d.id for d in selected]

    db = SessionLocal()
    try:
        run = PipelineRun(
            id=run_id,
            project_id=project_id,
            title=title or "Untitled PRD",
            requirement_details=requirement_details,
            persona_override=persona_override,
            output_style=output_style or "Plain English",
            document_ids=selected_ids,
            method="AI",
            stage_statuses={
                "ingestion": "pending",
                "framework": "pending",
                "checkpoint": "pending",
                "prd": "pending",
                "bdd": "pending",
                "jira_format": "pending",
                "wireframe": "pending",
                "ux_flow": "pending",
            },
        )
        db.add(run)
        project = db.query(Project).filter_by(id=project_id).first()
        project.status = "running"
        db.commit()
    finally:
        db.close()

    initial_state = {
        "project_id": project_id,
        "run_id": run_id,
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "storage_path": d.storage_path,
            }
            for d in selected
        ],
        "requirement_title": title or "",
        "requirement_details": requirement_details or "",
        "persona_override": persona_override or "",
        "output_style": output_style or "Plain English",
        "cleaned_content": "",
        "framework": {},
        "approval_status": "",
        "approval_notes": "",
        "prd_markdown": "",
        "prd_storage_path": "",
        "bdd_storage_path": "",
        "jira_storage_path": "",
        "wireframe_storage_path": "",
        "ux_flow_storage_path": "",
        "current_stage": "ingestion",
        "errors": [],
    }

    try:
        compiled_graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": run_id}},
        )
    except Exception as e:
        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=run_id).first()
            project = db.query(Project).filter_by(id=project_id).first()
            if run:
                run.error = str(e)
                run.current_stage = "failed"
            if project:
                project.status = "failed"
            db.commit()
        finally:
            db.close()

    return run_id


def get_run_status(run_id: str) -> PipelineRun | None:
    db = SessionLocal()
    try:
        return db.query(PipelineRun).filter_by(id=run_id).first()
    finally:
        db.close()


def get_latest_run(project_id: str) -> PipelineRun | None:
    db = SessionLocal()
    try:
        return (
            db.query(PipelineRun)
            .filter_by(project_id=project_id)
            .order_by(PipelineRun.started_at.desc())
            .first()
        )
    finally:
        db.close()


def get_runs(project_id: str) -> list[PipelineRun]:
    db = SessionLocal()
    try:
        return (
            db.query(PipelineRun)
            .filter_by(project_id=project_id)
            .order_by(PipelineRun.started_at.desc())
            .all()
        )
    finally:
        db.close()


def run_display_status(run: PipelineRun) -> str:
    """Derive a per-run status from its stage statuses (independent of the
    project-level status, which only tracks the most recent run)."""
    statuses = (run.stage_statuses or {}).values()
    if "failed" in statuses:
        return "failed"
    if "awaiting" in statuses:
        return "awaiting_approval"
    if run.completed_at or (run.stage_statuses or {}).get("ux_flow") == "complete":
        return "complete"
    if "running" in statuses:
        return "running"
    return "pending"


def regenerate_visuals(run_id: str, llm_settings: dict | None = None) -> None:
    """Re-run wireframe + UX flow nodes against an existing run, reusing the
    cached framework JSON and PRD markdown. Lets users iterate on the visuals
    without paying for framework + PRD generation again."""
    import json
    set_llm_override(llm_settings)
    from pipeline.nodes.wireframe import wireframe_node
    from pipeline.nodes.ux_flow import ux_flow_node

    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter_by(id=run_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")
        project_id = run.project_id

        fw_out = db.query(GeneratedOutput).filter_by(run_id=run_id, stage="framework").first()
        prd_out = db.query(GeneratedOutput).filter_by(run_id=run_id, stage="prd").first()
        if not fw_out or not prd_out:
            raise ValueError("Cannot regenerate visuals: run is missing framework or PRD output")

        # Remove prior visual outputs so we don't keep stale duplicates
        db.query(GeneratedOutput).filter(
            GeneratedOutput.run_id == run_id,
            GeneratedOutput.stage.in_(["wireframe", "ux_flow"]),
        ).delete(synchronize_session=False)

        # Reset stage statuses for the two stages we're about to re-run
        statuses = dict(run.stage_statuses or {})
        statuses["wireframe"] = "pending"
        statuses["ux_flow"] = "pending"
        run.stage_statuses = statuses
        run.completed_at = None  # ux_flow_node will re-set this on success
        run.error = None
        project = db.query(Project).filter_by(id=project_id).first()
        if project:
            project.status = "running"
        db.commit()

        framework = json.loads(fw_out.content)
        prd_markdown = prd_out.content
        title = run.title or ""
        details = run.requirement_details or ""
        persona = run.persona_override or ""
        style = run.output_style or "Plain English"
    finally:
        db.close()

    state = {
        "project_id": project_id,
        "run_id": run_id,
        "documents": [],
        "requirement_title": title,
        "requirement_details": details,
        "persona_override": persona,
        "output_style": style,
        "cleaned_content": "",
        "framework": framework,
        "approval_status": "approved",
        "approval_notes": "",
        "prd_markdown": prd_markdown,
        "prd_storage_path": "",
        "bdd_storage_path": "",
        "jira_storage_path": "",
        "wireframe_storage_path": "",
        "ux_flow_storage_path": "",
        "current_stage": "wireframe",
        "errors": [],
    }

    try:
        state = wireframe_node(state)
        state = ux_flow_node(state)
    except Exception:
        # The node itself records the failure in stage_statuses + project.status,
        # so we don't need to do anything beyond letting the UI poll and surface it.
        raise


def get_output(project_id: str, run_id: str, stage: str) -> GeneratedOutput | None:
    db = SessionLocal()
    try:
        return db.query(GeneratedOutput).filter_by(
            project_id=project_id, run_id=run_id, stage=stage
        ).first()
    finally:
        db.close()


# ── HITL (V2) ─────────────────────────────────────────────────────────────────

def approve_run(run_id: str, notes: str, edited_framework: dict) -> None:
    from pipeline.graph import compiled_graph

    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter_by(id=run_id).first()
        if run:
            run.approval_status = "approved"
            run.approval_notes = notes
            db.commit()
    finally:
        db.close()

    compiled_graph.invoke(
        {"approved": True, "notes": notes, "framework": edited_framework},
        config={"configurable": {"thread_id": run_id}},
    )


def reject_run(run_id: str, notes: str) -> None:
    from pipeline.graph import compiled_graph

    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter_by(id=run_id).first()
        if run:
            run.approval_status = "rejected"
            run.approval_notes = notes
            project = db.query(Project).filter_by(id=run.project_id).first()
            if project:
                project.status = "failed"
            db.commit()
    finally:
        db.close()

    compiled_graph.invoke(
        {"approved": False, "notes": notes},
        config={"configurable": {"thread_id": run_id}},
    )
