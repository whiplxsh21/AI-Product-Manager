import json
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from database import SessionLocal
from llm import get_main_llms, invoke_with_fallback
from models import GeneratedOutput, PipelineRun, Project
from pipeline.prompts import FRAMEWORK_PROMPT
from pipeline.state import PipelineState


def _loads_json(text: str) -> dict:
    """Parse JSON tolerantly — some models wrap output in markdown fences, add
    prose around it, leave trailing commas, emit unescaped quotes inside string
    values, or truncate large responses. We try strict parsing first, then a
    brace-extraction pass, then json_repair as a last resort so a single bad
    character doesn't fail the whole pipeline."""
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        start, end = s.find("{"), s.rfind("}")
        candidate = s[start:end + 1] if (start != -1 and end > start) else s
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Last resort: repair common LLM JSON defects (unescaped quotes,
            # trailing commas, truncated brackets) and parse the result.
            from json_repair import repair_json
            repaired = repair_json(candidate, return_objects=True)
            if isinstance(repaired, dict):
                return repaired
            raise


def _try_parse(text: str) -> dict | None:
    """Parse JSON tolerantly, returning None instead of raising so callers can
    decide whether to retry."""
    try:
        return _loads_json(text)
    except Exception:  # noqa: BLE001 — any parse/repair failure → retry path
        return None


def _is_usable_framework(fw) -> bool:
    """A framework is only usable if it carries at least one epic with stories —
    otherwise the BDD (Node 4) and Jira (Node 5) transforms produce empty files."""
    if not isinstance(fw, dict):
        return False
    epics = fw.get("epics")
    if not isinstance(epics, list) or not epics:
        return False
    return any(
        isinstance(e, dict) and isinstance(e.get("user_stories"), list) and e["user_stories"]
        for e in epics
    )


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

        # Parse + validate. A salvaged-but-incomplete framework (e.g. json_repair
        # closing a truncated/malformed response and dropping the "epics" array)
        # must NOT pass silently — that produces empty BDD stories and Jira
        # export downstream. Retry once with a corrective prompt, then fail loud.
        framework = _try_parse(response.content)
        if not _is_usable_framework(framework):
            retry_response = invoke_with_fallback(llms, [
                system_msg,
                human_msg,
                AIMessage(content=response.content),
                HumanMessage(content=(
                    "The previous response was not valid JSON or was missing the "
                    "required non-empty \"epics\" array (each epic needs "
                    "\"user_stories\"). Return ONLY one complete, valid JSON object "
                    "matching the schema exactly — no markdown fences, no preamble."
                )),
            ])
            framework = _try_parse(retry_response.content)

        if not _is_usable_framework(framework):
            raise ValueError(
                "Framework analysis returned no epics / user stories — the model "
                "output was incomplete or malformed. Please click Generate again."
            )

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
