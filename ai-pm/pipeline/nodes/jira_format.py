import json
from datetime import datetime

from database import SessionLocal
from models import GeneratedOutput, PipelineRun, Project
from pipeline.state import PipelineState
from storage import get_storage

PRIORITY_MAP = {
    "must-have": "Highest",
    "should-have": "High",
    "could-have": "Medium",
    "wont-have": "Low",
}

STORY_POINTS_MAP = {
    "S": 2,
    "M": 5,
    "L": 8,
    "XL": 13,
}


def _format_description(story: dict) -> str:
    parts = [story["story"], "", "Acceptance Criteria:"]
    for criterion in story.get("acceptance_criteria", []):
        parts.append(f"- {criterion}")
    return "\n".join(parts)


def _build_jira_export(framework: dict, project_id: str, run_id: str) -> dict:
    from config import config
    epics = []
    for epic in framework.get("epics", []):
        stories = []
        for story in epic.get("user_stories", []):
            summary = story["title"][:255]
            stories.append({
                "local_id": story["id"],
                "epic_local_id": epic["id"],
                "summary": summary,
                "description": _format_description(story),
                "issuetype": "Story",
                "priority": PRIORITY_MAP.get(story.get("priority", "could-have"), "Medium"),
                "story_points": STORY_POINTS_MAP.get(story.get("effort", "M"), 5),
                "labels": ["ai-pm-generated"],
            })
        epics.append({
            "local_id": epic["id"],
            "summary": f"{epic['id']}: {epic['title']}"[:255],
            "description": epic.get("description", ""),
            "issuetype": "Epic",
            "labels": ["ai-pm-generated"],
            "stories": stories,
        })

    return {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "project_id": project_id,
            "run_id": run_id,
            "jira_project_key": config.jira_project_key or None,
        },
        "epics": epics,
    }


def jira_format_node(state: PipelineState) -> PipelineState:
    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
        statuses = dict(run.stage_statuses)
        statuses["jira_format"] = "running"
        run.stage_statuses = statuses
        run.current_stage = "jira_format"
        db.commit()
    finally:
        db.close()

    try:
        jira_export = _build_jira_export(state["framework"], state["project_id"], state["run_id"])
        jira_json = json.dumps(jira_export, indent=2)

        storage = get_storage()
        jira_path = storage.save(state["project_id"], f"{state['run_id']}_jira_export.json", jira_json)

        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
            output = GeneratedOutput(
                project_id=state["project_id"],
                run_id=state["run_id"],
                stage="jira_format",
                content=jira_json,
            )
            db.add(output)
            statuses = dict(run.stage_statuses)
            statuses["jira_format"] = "complete"
            run.stage_statuses = statuses
            db.commit()
        finally:
            db.close()

        return {**state, "jira_storage_path": jira_path}

    except Exception as e:
        errors = list(state.get("errors", []))
        errors.append(f"Jira formatting failed: {str(e)}")
        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
            project = db.query(Project).filter_by(id=state["project_id"]).first()
            statuses = dict(run.stage_statuses)
            statuses["jira_format"] = "failed"
            run.stage_statuses = statuses
            run.current_stage = "failed"
            run.error = str(e)
            project.status = "failed"
            db.commit()
        finally:
            db.close()
        raise
