import json
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from database import SessionLocal
from llm import get_main_llms, invoke_with_fallback
from models import GeneratedOutput, PipelineRun, Project
from pipeline.prompts import PRD_PROMPT
from pipeline.state import PipelineState
from storage import get_storage


def prd_node(state: PipelineState) -> PipelineState:
    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
        statuses = dict(run.stage_statuses)
        statuses["prd"] = "running"
        run.stage_statuses = statuses
        run.current_stage = "prd"
        db.commit()
    finally:
        db.close()

    try:
        today = datetime.utcnow().strftime("%B %d, %Y")
        prompt = PRD_PROMPT.replace("{date}", today)

        llms = get_main_llms(temperature=0.4)
        system_msg = SystemMessage(content=prompt)
        user_content = f"""REQUIREMENT TITLE: {state.get('requirement_title') or 'None'}
REQUIREMENT BRIEF: {state.get('requirement_details') or 'None'}
PRIMARY PERSONA: {state.get('persona_override') or 'None'}
OUTPUT STYLE: {state.get('output_style') or 'Plain English'}

Framework analysis:
{json.dumps(state['framework'], indent=2)}

Approval notes from reviewer:
{state.get('approval_notes') or 'None'}
"""
        human_msg = HumanMessage(content=user_content)
        response = invoke_with_fallback(llms, [system_msg, human_msg])
        prd_markdown = response.content.strip()

        storage = get_storage()
        prd_path = storage.save(state["project_id"], f"{state['run_id']}_prd.md", prd_markdown)

        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
            output = GeneratedOutput(
                project_id=state["project_id"],
                run_id=state["run_id"],
                stage="prd",
                content=prd_markdown,
            )
            db.add(output)
            statuses = dict(run.stage_statuses)
            statuses["prd"] = "complete"
            run.stage_statuses = statuses
            # Note: project.status = "complete" + run.completed_at are set by
            # the final node (ux_flow), so the UI only flips to complete after
            # every artifact (BDD, Jira, wireframe, UX flow) is done.
            db.commit()
        finally:
            db.close()

        return {**state, "prd_markdown": prd_markdown, "prd_storage_path": prd_path,
                "current_stage": "prd"}

    except Exception as e:
        errors = list(state.get("errors", []))
        errors.append(f"PRD generation failed: {str(e)}")
        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
            project = db.query(Project).filter_by(id=state["project_id"]).first()
            statuses = dict(run.stage_statuses)
            statuses["prd"] = "failed"
            run.stage_statuses = statuses
            run.current_stage = "failed"
            run.error = str(e)
            project.status = "failed"
            db.commit()
        finally:
            db.close()
        raise
