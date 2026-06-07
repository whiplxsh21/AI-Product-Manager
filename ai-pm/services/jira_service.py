"""Business logic for the Jira integration.

The UI (app.py) calls only these functions — never `JiraClient` directly. This
mirrors how the rest of the app keeps Streamlit free of integration details.

Phase 1: connection settings, test_connection, list_projects. Pushing issues
arrives in Phase 2.
"""
from __future__ import annotations

import services.auth_service as auth
from integrations.jira import JiraClient, JiraError, normalize_site_url

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
