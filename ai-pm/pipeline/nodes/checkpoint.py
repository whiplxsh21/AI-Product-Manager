from database import SessionLocal
from models import PipelineRun
from pipeline.state import PipelineState


def checkpoint_node(state: PipelineState) -> PipelineState:
    """Records the framework stage as complete and auto-approves so the pipeline
    proceeds to the PRD. Human review happens at the PRD stage (see prd_review)."""
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
        "approval_notes": "",
        "current_stage": "checkpoint",
    }
