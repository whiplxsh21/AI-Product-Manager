"""Business logic for the Jira integration.

The UI (app.py) calls only these functions — never `JiraClient` directly. This
mirrors how the rest of the app keeps Streamlit free of integration details.

Phase 1: connection settings, test_connection, list_projects. Pushing issues
arrives in Phase 2.
"""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime

import services.auth_service as auth
from database import SessionLocal
from integrations.jira import JiraClient, JiraError, normalize_site_url
from models import GeneratedOutput, JiraSyncRecord

# Keys we persist in the user's encrypted Jira settings blob.
SETTINGS_FIELDS = ("site_url", "email", "project_key", "story_points_field")
SECRET_FIELDS = ("api_token",)


def get_settings(user_id: str) -> dict:
    """The user's saved Jira settings (api_token included, decrypted)."""
    return auth.get_jira_settings(user_id)


def is_configured(user_id: str) -> bool:
    """True once site/email/token are all present — enough to talk to Jira."""
    s = get_settings(user_id)
    return bool(s.get("site_url") and s.get("email") and s.get("api_token"))


def _client_from_settings(s: dict) -> JiraClient:
    return JiraClient(s.get("site_url", ""), s.get("email", ""), s.get("api_token", ""))


def save_settings(user_id: str, *, site_url: str, email: str,
                  api_token: str | None, project_key: str | None = None) -> None:
    """Persist Jira settings (encrypted). A blank api_token keeps the saved one,
    matching how LLM keys behave in Settings."""
    current = get_settings(user_id)
    new = dict(current)
    new["site_url"] = normalize_site_url(site_url) if site_url else current.get("site_url", "")
    new["email"] = (email or "").strip()
    if project_key is not None:
        new["project_key"] = project_key.strip()
    if api_token and api_token.strip():
        new["api_token"] = api_token.strip()
    auth.save_jira_settings(user_id, new)


def save_project_selection(user_id: str, project_key: str) -> None:
    """Persist the chosen project and (best-effort) the story-points field id."""
    s = get_settings(user_id)
    s["project_key"] = (project_key or "").strip()
    try:
        s["story_points_field"] = _client_from_settings(s).discover_story_points_field() or ""
    except JiraError:
        s["story_points_field"] = s.get("story_points_field", "")
    auth.save_jira_settings(user_id, s)


def test_connection(user_id: str) -> dict:
    """Verify the saved credentials. Returns the Jira user on success;
    raises JiraError on failure (the UI shows the message)."""
    s = get_settings(user_id)
    if not (s.get("site_url") and s.get("email") and s.get("api_token")):
        raise JiraError("Jira is not fully configured. Enter site URL, email, and API token first.")
    return _client_from_settings(s).verify()


def list_projects(user_id: str) -> list[dict]:
    """Projects visible to the user, for the project picker."""
    s = get_settings(user_id)
    if not (s.get("site_url") and s.get("email") and s.get("api_token")):
        raise JiraError("Configure and test the Jira connection first.")
    return _client_from_settings(s).list_projects()


# ── Push (Phase 2) ────────────────────────────────────────────────────────────

# In-memory push progress, keyed by run_id. The push runs in a background thread
# in the same process as the Streamlit UI, which polls get_push_status(). Same
# single-process assumption the LLM-override contextvar relies on.
_push_status: dict[str, dict] = {}


def get_push_status(run_id: str) -> dict | None:
    return _push_status.get(run_id)


def get_sync_records(run_id: str) -> list[JiraSyncRecord]:
    db = SessionLocal()
    try:
        return (
            db.query(JiraSyncRecord)
            .filter_by(run_id=run_id)
            .order_by(JiraSyncRecord.created_at)
            .all()
        )
    finally:
        db.close()


def _load_export(run_id: str) -> tuple[dict, str | None]:
    """Return (export_json, project_id) from the jira_format output of a run."""
    db = SessionLocal()
    try:
        out = (
            db.query(GeneratedOutput)
            .filter_by(run_id=run_id, stage="jira_format")
            .order_by(GeneratedOutput.created_at.desc())
            .first()
        )
        if not out:
            raise JiraError("No Jira export found for this run. Run the pipeline first.")
        return json.loads(out.content), out.project_id
    finally:
        db.close()


def _save_record(run_id, project_id, local_id, issuetype, jira_key, jira_url, status, detail):
    db = SessionLocal()
    try:
        db.add(JiraSyncRecord(
            id=str(uuid.uuid4()),
            run_id=run_id,
            project_id=project_id,
            local_id=local_id,
            issuetype=issuetype,
            jira_key=jira_key,
            jira_url=jira_url,
            status=status,
            detail=detail,
            created_at=datetime.utcnow(),
        ))
        db.commit()
    finally:
        db.close()


def start_push(user_id: str, run_id: str) -> None:
    """Kick off a push in a background thread (non-blocking for the UI)."""
    _push_status[run_id] = {"state": "running", "created": 0, "skipped": 0,
                            "failed": 0, "error": None}
    threading.Thread(target=_push_worker, args=(user_id, run_id), daemon=True).start()


def _push_worker(user_id: str, run_id: str) -> None:
    try:
        push_run(user_id, run_id)
        st = _push_status.get(run_id, {})
        st["state"] = "done"
        _push_status[run_id] = st
    except Exception as e:  # noqa: BLE001 — surface any failure to the UI
        st = _push_status.get(run_id, {})
        st["state"] = "error"
        st["error"] = str(e)
        _push_status[run_id] = st


def push_run(user_id: str, run_id: str) -> None:
    """Create the run's epics and stories in Jira, idempotently.

    Already-created issues (recorded by a prior push) are skipped. Story points
    field is taken from the saved settings (discovered at project-selection time).
    """
    settings = get_settings(user_id)
    if not (settings.get("site_url") and settings.get("email") and settings.get("api_token")):
        raise JiraError("Jira is not configured. Add your connection in Settings.")
    project_key = settings.get("project_key")
    if not project_key:
        raise JiraError("No target Jira project selected. Pick one in Settings.")

    client = _client_from_settings(settings)
    sp_field = settings.get("story_points_field") or None

    export, project_id = _load_export(run_id)
    status = _push_status.setdefault(run_id, {"state": "running", "created": 0,
                                              "skipped": 0, "failed": 0, "error": None})

    # Idempotency: local_id → existing successful record.
    already = {r.local_id: r for r in get_sync_records(run_id) if r.status == "created"}
    epic_key_by_local = {lid: r.jira_key for lid, r in already.items()}

    for epic in export.get("epics", []):
        elid = epic["local_id"]
        if elid in already:
            status["skipped"] += 1
        else:
            try:
                res = client.create_epic(
                    project_key, epic.get("summary", ""),
                    epic.get("description", ""), epic.get("labels"),
                )
                epic_key_by_local[elid] = res["key"]
                _save_record(run_id, project_id, elid, "Epic",
                             res["key"], res["url"], "created", None)
                status["created"] += 1
            except JiraError as e:
                _save_record(run_id, project_id, elid, "Epic",
                             None, None, "failed", e.message)
                status["failed"] += 1

        epic_key = epic_key_by_local.get(elid)
        for story in epic.get("stories", []):
            slid = story["local_id"]
            if slid in already:
                status["skipped"] += 1
                continue
            if not epic_key:
                _save_record(run_id, project_id, slid, "Story", None, None,
                             "skipped", "Parent epic was not created.")
                status["skipped"] += 1
                continue
            try:
                res = client.create_story(
                    project_key, story.get("summary", ""), story.get("description", ""),
                    epic_key=epic_key, priority=story.get("priority"),
                    story_points=story.get("story_points"),
                    story_points_field=sp_field, labels=story.get("labels"),
                )
                detail = "; ".join(res["warnings"]) or None
                _save_record(run_id, project_id, slid, "Story",
                             res["key"], res["url"], "created", detail)
                status["created"] += 1
            except JiraError as e:
                _save_record(run_id, project_id, slid, "Story",
                             None, None, "failed", e.message)
                status["failed"] += 1
