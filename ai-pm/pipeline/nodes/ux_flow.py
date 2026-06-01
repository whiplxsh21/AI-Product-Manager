import re
import time
from datetime import datetime

import requests
from langchain_core.messages import HumanMessage, SystemMessage

from database import SessionLocal
from llm import get_main_llms, invoke_with_fallback
from models import GeneratedOutput, PipelineRun, Project
from pipeline.prompts import UX_FLOW_PROMPT
from pipeline.state import PipelineState
from storage import get_storage

_KROKI_URL = "https://kroki.io/mermaid/svg"


def _strip_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s).strip()
    return s


def _mermaid_to_svg(mermaid: str) -> str:
    """POST the diagram source to kroki.io and return SVG. Retries on transient
    failures (network blips, brief 5xx) before letting the caller fall back."""
    last_exc = None
    for attempt in range(3):
        try:
            r = requests.post(_KROKI_URL, data=mermaid.encode("utf-8"),
                              headers={"Content-Type": "text/plain"}, timeout=30)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_exc = e
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
            else:
                raise last_exc
    raise last_exc


def _fallback_svg(mermaid: str, error: str) -> str:
    """Wrap the raw mermaid source in a simple SVG with a notice so the user
    still gets something previewable + downloadable when kroki is unreachable."""
    lines = mermaid.splitlines() or [""]
    line_h = 16
    height = 60 + line_h * len(lines) + 40
    body_lines = "\n".join(
        f'<text x="20" y="{60 + i * line_h}" font-family="monospace" font-size="12" fill="#111827">'
        f'{line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</text>'
        for i, line in enumerate(lines)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" '
        f'viewBox="0 0 900 {height}">'
        f'<rect width="900" height="{height}" fill="#fff7ed"/>'
        f'<text x="20" y="30" font-family="Inter, Arial" font-size="14" font-weight="700" fill="#9a3412">'
        f'Mermaid render unavailable — raw source shown below.</text>'
        f'<text x="20" y="48" font-family="Inter, Arial" font-size="11" fill="#9a3412">'
        f'Paste into mermaid.live or any Mermaid renderer. ({error[:80]})</text>'
        f'{body_lines}'
        f'</svg>'
    )


def ux_flow_node(state: PipelineState) -> PipelineState:
    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
        statuses = dict(run.stage_statuses)
        statuses["ux_flow"] = "running"
        run.stage_statuses = statuses
        run.current_stage = "ux_flow"
        db.commit()
    finally:
        db.close()

    try:
        import json
        llms = get_main_llms(temperature=0.3)
        system_msg = SystemMessage(content=UX_FLOW_PROMPT)
        user_content = f"""PRIMARY PERSONA: {state.get('persona_override') or 'None'}

Framework analysis:
{json.dumps(state['framework'], indent=2)}
"""
        response = invoke_with_fallback(llms, [system_msg, HumanMessage(content=user_content)])
        mermaid = _strip_fences(response.content)

        # Render via kroki; on any failure fall back to a notice SVG so the
        # pipeline always produces something the user can preview / download.
        try:
            svg = _mermaid_to_svg(mermaid)
        except Exception as render_err:
            svg = _fallback_svg(mermaid, str(render_err))

        storage = get_storage()
        path = storage.save(state["project_id"], f"{state['run_id']}_ux_flow.svg", svg)

        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
            project = db.query(Project).filter_by(id=state["project_id"]).first()
            output = GeneratedOutput(
                project_id=state["project_id"],
                run_id=state["run_id"],
                stage="ux_flow",
                content=svg,
            )
            db.add(output)
            statuses = dict(run.stage_statuses)
            statuses["ux_flow"] = "complete"
            run.stage_statuses = statuses
            run.completed_at = datetime.utcnow()
            project.status = "complete"
            db.commit()
        finally:
            db.close()

        return {**state, "ux_flow_storage_path": path, "current_stage": "ux_flow"}

    except Exception as e:
        errors = list(state.get("errors", []))
        errors.append(f"UX flow generation failed: {str(e)}")
        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter_by(id=state["run_id"]).first()
            project = db.query(Project).filter_by(id=state["project_id"]).first()
            statuses = dict(run.stage_statuses)
            statuses["ux_flow"] = "failed"
            run.stage_statuses = statuses
            run.current_stage = "failed"
            run.error = str(e)
            project.status = "failed"
            db.commit()
        finally:
            db.close()
        raise
