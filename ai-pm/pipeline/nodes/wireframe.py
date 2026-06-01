import json

from langchain_core.messages import HumanMessage, SystemMessage

from database import SessionLocal
from llm import get_main_llms, invoke_with_fallback
from models import GeneratedOutput, PipelineRun, Project
from pipeline.nodes.framework import _loads_json
from pipeline.prompts import WIREFRAME_PROMPT
from pipeline.state import PipelineState
from pipeline.wireframe_render import render_wireframes
from storage import get_storage


def wireframe_node(state: PipelineState) -> PipelineState:
    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
        statuses = dict(run.stage_statuses)
        statuses["wireframe"] = "running"
        run.stage_statuses = statuses
        run.current_stage = "wireframe"
        db.commit()
    finally:
        db.close()

    try:
        llms = get_main_llms(temperature=0.3)
        system_msg = SystemMessage(content=WIREFRAME_PROMPT)
        user_content = f"""PRIMARY PERSONA: {state.get('persona_override') or 'None'}

Framework analysis:
{json.dumps(state['framework'], indent=2)}

PRD (for additional context):
{state.get('prd_markdown', '')[:4000]}
"""
        response = invoke_with_fallback(llms, [system_msg, HumanMessage(content=user_content)])

        try:
            schema = _loads_json(response.content)
        except json.JSONDecodeError:
            retry = invoke_with_fallback(llms, [
                system_msg,
                HumanMessage(content=user_content),
                HumanMessage(content="The previous response was not valid JSON. Return ONLY a valid JSON object matching the schema with no other text, no markdown fences."),
            ])
            schema = _loads_json(retry.content)

        svg = render_wireframes(schema)

        storage = get_storage()
        path = storage.save(state["project_id"], f"{state['run_id']}_wireframe.svg", svg)

        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
            output = GeneratedOutput(
                project_id=state["project_id"],
                run_id=state["run_id"],
                stage="wireframe",
                content=svg,
            )
            db.add(output)
            statuses = dict(run.stage_statuses)
            statuses["wireframe"] = "complete"
            run.stage_statuses = statuses
            db.commit()
        finally:
            db.close()

        return {**state, "wireframe_storage_path": path, "current_stage": "wireframe"}

    except Exception as e:
        errors = list(state.get("errors", []))
        errors.append(f"Wireframe generation failed: {str(e)}")
        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
            project = db.query(Project).filter_by(id=state["project_id"]).first()
            statuses = dict(run.stage_statuses)
            statuses["wireframe"] = "failed"
            run.stage_statuses = statuses
            run.current_stage = "failed"
            run.error = str(e)
            project.status = "failed"
            db.commit()
        finally:
            db.close()
        raise
