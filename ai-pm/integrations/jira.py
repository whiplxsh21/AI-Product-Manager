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
