"""Jira Cloud REST API client.

This is the ONLY module in the project that talks to Jira over HTTP. Everything
else (services, UI) goes through `JiraClient`. Same discipline as `llm.py` for
LLM providers and `storage.py` for the filesystem.

Auth model (Jira Cloud): HTTP Basic with the user's Atlassian account email and
an API token they create at id.atlassian.com. We use REST API **v2** (not v3)
on purpose: v3 requires descriptions in Atlassian Document Format (a JSON tree),
while v2 accepts plain-text descriptions — which is exactly what our pipeline
produces, so no conversion is needed.

Phase 1 covers connection + discovery (verify, list_projects,
discover_story_points_field). Issue creation (create_epic/create_story) arrives
in Phase 2.
"""
from __future__ import annotations

import json

import requests
from requests.auth import HTTPBasicAuth

_TIMEOUT = 30  # seconds per request


class JiraError(Exception):
    """A Jira call failed. Carries a human-readable message for the UI and,
    when available, the HTTP status and raw response body for debugging."""

    def __init__(self, message: str, status: int | None = None, body: str | None = None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.body = body


def _parse_field_errors(body: str | None) -> tuple[dict, list]:
    """Pull Jira's per-field errors and top-level messages out of a 400 body.
    Returns ({field_id: message}, [error_messages])."""
    if not body:
        return {}, []
    try:
        data = json.loads(body)
    except (ValueError, TypeError):
        return {}, []
    if not isinstance(data, dict):
        return {}, []
    return data.get("errors", {}) or {}, data.get("errorMessages", []) or []


def normalize_site_url(raw: str) -> str:
    """Turn whatever the user typed into a clean base URL.

    Accepts 'dhruv.atlassian.net', 'https://dhruv.atlassian.net/', or a URL with
    a trailing '/rest/...' path, and returns 'https://dhruv.atlassian.net'.
    """
    site = (raw or "").strip()
    if not site:
        raise JiraError("Jira site URL is empty.")
    if site.startswith("http://"):
        site = "https://" + site[len("http://"):]
    elif not site.startswith("https://"):
        site = "https://" + site
    # Strip everything from '/rest' onward and any trailing slash.
    site = site.split("/rest", 1)[0].rstrip("/")
    return site


class JiraClient:
    def __init__(self, site_url: str, email: str, api_token: str):
        self.site_url = normalize_site_url(site_url)
        self.email = (email or "").strip()
        self._token = (api_token or "").strip()
        if not self.email or not self._token:
            raise JiraError("Jira email and API token are both required.")

        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(self.email, self._token)
        self._session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    # ── low-level request helper ─────────────────────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        url = f"{self.site_url}/rest/api/2/{path.lstrip('/')}"
        try:
            resp = self._session.get(url, params=params, timeout=_TIMEOUT)
        except requests.RequestException as e:
            raise JiraError(f"Could not reach Jira at {self.site_url}: {e}") from e
        return self._handle(resp)

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.site_url}/rest/api/2/{path.lstrip('/')}"
        try:
            resp = self._session.post(url, json=payload, timeout=_TIMEOUT)
        except requests.RequestException as e:
            raise JiraError(f"Could not reach Jira at {self.site_url}: {e}") from e
        return self._handle(resp)

    def _browse(self, key: str) -> str:
        return f"{self.site_url}/browse/{key}"

    def _handle(self, resp: requests.Response) -> dict | list:
        if resp.status_code == 401:
            raise JiraError(
                "Authentication failed (401). Check the email matches the account "
                "and the API token is correct and not revoked.",
                status=401, body=resp.text,
            )
        if resp.status_code == 403:
            raise JiraError(
                "Permission denied (403). This account may lack access to the "
                "requested Jira resource.",
                status=403, body=resp.text,
            )
        if resp.status_code == 404:
            raise JiraError(
                "Not found (404). Double-check the Jira site URL.",
                status=404, body=resp.text,
            )
        if resp.status_code >= 400:
            raise JiraError(
                f"Jira returned an error ({resp.status_code}).",
                status=resp.status_code, body=resp.text,
            )
        try:
            return resp.json()
        except ValueError:
            # A 200 that isn't JSON almost always means the site URL is wrong and
            # we hit a login/redirect HTML page rather than the API.
            raise JiraError(
                "Jira returned a non-JSON response. The site URL is probably "
                "wrong — it should look like https://yourcompany.atlassian.net."
            )

    # ── public API ───────────────────────────────────────────────────────────

    def verify(self) -> dict:
        """Confirm credentials work. Returns the current user.
        GET /rest/api/2/myself"""
        data = self._get("myself")
        return {
            "account_id": data.get("accountId"),
            "display_name": data.get("displayName"),
            "email": data.get("emailAddress"),
        }

    def list_projects(self) -> list[dict]:
        """All projects visible to this account (paginated).
        GET /rest/api/2/project/search"""
        projects: list[dict] = []
        start_at = 0
        while True:
            page = self._get("project/search", params={
                "startAt": start_at, "maxResults": 50,
            })
            values = page.get("values", []) if isinstance(page, dict) else []
            for p in values:
                projects.append({
                    "key": p.get("key"),
                    "name": p.get("name"),
                    "id": p.get("id"),
                })
            if isinstance(page, dict) and page.get("isLast", True):
                break
            start_at += len(values)
            if not values:
                break
        return projects

    def discover_story_points_field(self) -> str | None:
        """Find the custom field id that holds story points on this instance.
        There is no universal field — its id varies per site — so we match by
        name. Returns the field id (e.g. 'customfield_10016') or None.
        GET /rest/api/2/field"""
        fields = self._get("field")
        if not isinstance(fields, list):
            return None
        wanted = {"story points", "story point estimate"}
        for f in fields:
            name = (f.get("name") or "").strip().lower()
            if name in wanted:
                return f.get("id")
        return None

    def discover_epic_link_field(self) -> str | None:
        """Legacy 'Epic Link' custom field id, used to parent stories in older
        company-managed projects that reject the modern `parent` field. Cached
        on the instance. GET /rest/api/2/field"""
        if hasattr(self, "_epic_link_field"):
            return self._epic_link_field
        result = None
        fields = self._get("field")
        if isinstance(fields, list):
            for f in fields:
                if (f.get("name") or "").strip().lower() == "epic link":
                    result = f.get("id")
                    break
        self._epic_link_field = result
        return result

    def create_epic(self, project_key: str, summary: str,
                    description: str = "", labels: list[str] | None = None) -> dict:
        """Create an Epic. POST /rest/api/2/issue → {key, url}"""
        fields = {
            "project": {"key": project_key},
            "summary": (summary or "")[:255],
            "description": description or "",
            "issuetype": {"name": "Epic"},
            "labels": labels or [],
        }
        data = self._post("issue", {"fields": fields})
        return {"key": data["key"], "url": self._browse(data["key"])}

    def create_story(self, project_key: str, summary: str, description: str,
                     epic_key: str | None = None, priority: str | None = None,
                     story_points: float | None = None,
                     story_points_field: str | None = None,
                     labels: list[str] | None = None) -> dict:
        """Create a Story under an epic. POST /rest/api/2/issue.

        Core fields (project/summary/description/issuetype/labels) are required.
        Epic link, priority, and story points are best-effort: if Jira rejects
        any of them (e.g. not on the project's create screen), we strip/adapt the
        offending field and retry rather than failing the whole story. Returns
        {key, url, warnings}."""
        warnings: list[str] = []
        fields = {
            "project": {"key": project_key},
            "summary": (summary or "")[:255],
            "description": description or "",
            "issuetype": {"name": "Story"},
            "labels": labels or [],
        }
        if epic_key:
            fields["parent"] = {"key": epic_key}
        if priority:
            fields["priority"] = {"name": priority}
        if story_points is not None and story_points_field:
            fields[story_points_field] = story_points

        epic_link_field: str | None = None  # set once we fall back to Epic Link

        # Progressively drop/adapt offending optional fields (max a few attempts).
        for _ in range(4):
            try:
                data = self._post("issue", {"fields": fields})
                return {"key": data["key"], "url": self._browse(data["key"]),
                        "warnings": warnings}
            except JiraError as e:
                if e.status != 400:
                    raise
                errs, msgs = _parse_field_errors(e.body)
                changed = False

                if "priority" in errs and "priority" in fields:
                    warnings.append("Priority not set (field unavailable on this project).")
                    fields.pop("priority")
                    changed = True

                if story_points_field and story_points_field in errs and story_points_field in fields:
                    warnings.append("Story points not set (field unavailable on this project).")
                    fields.pop(story_points_field)
                    changed = True

                if "parent" in errs and "parent" in fields:
                    fields.pop("parent")
                    epic_link_field = self.discover_epic_link_field()
                    if epic_link_field:
                        fields[epic_link_field] = epic_key
                        warnings.append("Linked to epic via legacy Epic Link field.")
                    else:
                        warnings.append("Could not link to epic; created unparented.")
                    changed = True
                elif epic_link_field and epic_link_field in errs and epic_link_field in fields:
                    fields.pop(epic_link_field)
                    warnings.append("Could not link to epic; created unparented.")
                    changed = True

                if not changed:
                    detail = "; ".join(msgs) \
                        or "; ".join(f"{k}: {v}" for k, v in errs.items()) \
                        or e.message
                    raise JiraError(f"Story create failed: {detail}", status=400, body=e.body)

        raise JiraError("Story create failed after multiple field adjustments.")
