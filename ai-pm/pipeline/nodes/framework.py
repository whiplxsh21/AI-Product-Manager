import json
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from database import SessionLocal
from llm import get_main_llms, invoke_with_fallback
from models import GeneratedOutput, PipelineRun, Project
from pipeline.prompts import FRAMEWORK_PROMPT
from pipeline.state import PipelineState


def _loads_json(text: str) -> dict:
    """Parse JSON tolerantly — some models wrap output in markdown fences or add
    prose around it despite instructions not to."""
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        start, end = s.find("{"), s.rfind("}")
        if start != -1 and end > start:
            return json.loads(s[start:end + 1])
        raise


def framework_node(state: PipelineState) -> PipelineState:
    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
        statuses = dict(run.stage_statuses)
        statuses["framework"] = "running"
        run.stage_statuses = statuses
        run.current_stage = "framework"
        db.commit()
    finally:
        db.close()

    try:
        llms = get_main_llms(temperature=0.3)
        system_msg = SystemMessage(content=FRAMEWORK_PROMPT)

        brief_parts = []
        if state.get("requirement_title"):
            brief_parts.append(f"REQUIREMENT TITLE: {state['requirement_title']}")
        if state.get("requirement_details"):
            brief_parts.append(f"REQUIREMENT BRIEF:\n{state['requirement_details']}")
        if state.get("persona_override"):
            brief_parts.append(f"PRIMARY PERSONA: {state['persona_override']}")
        brief = ("\n\n".join(brief_parts) + "\n\n") if brief_parts else ""

        human_msg = HumanMessage(
            content=f"{brief}Here is the cleaned meeting document:\n\n{state['cleaned_content']}"
        )

        response = invoke_with_fallback(llms, [system_msg, human_msg])

        try:
            framework = _loads_json(response.content)
        except json.JSONDecodeError:
            retry_response = invoke_with_fallback(llms, [
                system_msg,
                human_msg,
                AIMessage(content=response.content),
                HumanMessage(content="The previous response was not valid JSON. Return ONLY a valid JSON object with no other text, no markdown fences, no preamble."),
            ])
            framework = _loads_json(retry_response.content)

        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
            output = GeneratedOutput(
                project_id=state["project_id"],
                run_id=state["run_id"],
                stage="framework",
                content=json.dumps(framework, indent=2),
            )
            db.add(output)
            statuses = dict(run.stage_statuses)
            statuses["framework"] = "complete"
            run.stage_statuses = statuses
            db.commit()
        finally:
            db.close()

        return {**state, "framework": framework, "current_stage": "framework"}

    except Exception as e:
        errors = list(state.get("errors", []))
        errors.append(f"Framework analysis failed: {str(e)}")
        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
            project = db.query(Project).filter_by(id=state["project_id"]).first()
            statuses = dict(run.stage_statuses)
            statuses["framework"] = "failed"
            run.stage_statuses = statuses
            run.current_stage = "failed"
            run.error = str(e)
            project.status = "failed"
            db.commit()
        finally:
            db.close()
        raise
