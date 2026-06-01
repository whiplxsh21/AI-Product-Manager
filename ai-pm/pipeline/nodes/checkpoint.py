import json

from database import SessionLocal
from models import GeneratedOutput, PipelineRun, Project
from pipeline.state import PipelineState
from config import config


def checkpoint_node(state: PipelineState) -> PipelineState:
    if not config.hitl_enabled:
        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
            statuses = dict(run.stage_statuses)
            statuses["checkpoint"] = "complete"
            run.stage_statuses = statuses
            run.approval_status = "not_required"
            db.commit()
        finally:
            db.close()

        return {
            **state,
            "approval_status": "auto_approved",
            "approval_notes": "Auto-approved — HITL_ENABLED is false",
            "current_stage": "checkpoint",
        }

    # V2 HITL path
    from langgraph.types import interrupt

    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
        project = db.query(Project).filter_by(id=state["project_id"]).first()
        statuses = dict(run.stage_statuses)
        statuses["checkpoint"] = "awaiting"
        run.stage_statuses = statuses
        run.approval_status = "pending"
        project.status = "awaiting_approval"
        db.commit()
    finally:
        db.close()

    human_review = interrupt({
        "message": "Review the framework before PRD generation.",
        "framework": state["framework"],
    })

    if not human_review.get("approved", False):
        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
            project = db.query(Project).filter_by(id=state["project_id"]).first()
            run.approval_status = "rejected"
            run.approval_notes = human_review.get("notes", "")
            project.status = "failed"
            db.commit()
        finally:
            db.close()
        raise ValueError("Pipeline rejected by reviewer.")

    updated_framework = human_review.get("framework", state["framework"])
    notes = human_review.get("notes", "")

    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
        statuses = dict(run.stage_statuses)
        statuses["checkpoint"] = "complete"
        run.stage_statuses = statuses
        run.approval_status = "approved"
        run.approval_notes = notes
        output = db.query(GeneratedOutput).filter_by(
            run_id=state["run_id"], stage="framework"
        ).first()
        if output:
            output.content = json.dumps(updated_framework, indent=2)
        db.commit()
    finally:
        db.close()

    return {
        **state,
        "framework": updated_framework,
        "approval_status": "approved",
        "approval_notes": notes,
    }
