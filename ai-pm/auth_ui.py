"""Streamlit auth gate: login, forgot-password, and reset-password screens.

When AUTH_ENABLED is false the gate is a no-op so the app runs open locally.
When true, ensure_authenticated() blocks the app until the user signs in.
"""
import time
from datetime import datetime, timedelta

import streamlit as st
import extra_streamlit_components as stx

import crypto
from config import config
import services.auth_service as auth
import services.email_service as email_svc

# Browser cookie used to keep users logged in across page refreshes (Streamlit
# session_state is wiped on refresh). The cookie holds a Fernet-encrypted token,
# not the raw user id, so it can't be forged without APP_SECRET_KEY.
_COOKIE_NAME = "pmp_session"
_COOKIE_TTL_DAYS = 7


def _make_cookie_manager() -> "stx.CookieManager":
    """Create a fresh CookieManager each run. The component must re-render on
    every run to communicate with the browser; caching the instance across runs
    leaves it stale (reads return nothing, writes don't land)."""
    return stx.CookieManager(key="pmp_cookies")


def _write_session_cookie(cm, user_id: str) -> None:
    exp = time.time() + _COOKIE_TTL_DAYS * 86400
    token = crypto.encrypt_json({"uid": user_id, "exp": exp})
    cm.set(_COOKIE_NAME, token,
           expires_at=datetime.now() + timedelta(days=_COOKIE_TTL_DAYS))


def current_user() -> dict | None:
    return st.session_state.get("auth_user")


def current_owner_id() -> str | None:
    """Project owner scope for the active session. None means "see everything"
    (auth disabled / local dev)."""
    user = current_user()
    return user["id"] if user else None


def current_llm_settings() -> dict | None:
    return st.session_state.get("llm_settings") or None


def can_access(project) -> bool:
    """Whether the current session may view/edit this project."""
    if not config.auth_enabled:
        return True
    user = current_user()
    if not user:
        return False
    # Projects created before auth existed have no owner — treat as accessible.
    return project.owner_id in (None, user["id"])


def _login(user) -> None:
    # Only sets session state. The cookie is written by ensure_authenticated()
    # on the next run (a clean render pass), because writing it here and then
    # immediately rerunning drops the browser-side write.
    st.session_state.auth_user = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }
    st.session_state.llm_settings = auth.get_llm_settings(user.id)
    st.session_state.pop("_cookie_written", None)  # trigger a fresh cookie write


def logout() -> None:
    # Defer cookie deletion to the next run's ensure_authenticated(), where it
    # runs on a clean pass (deleting + immediately rerunning drops the write).
    st.session_state["_do_logout"] = True
    for k in ("auth_user", "llm_settings", "selected_project_id",
              "view_run_id", "run_id", "_cookie_written"):
        st.session_state.pop(k, None)


def _reset_link(token: str) -> str:
    base = (config.app_base_url or "").rstrip("/")
    return f"{base}/?reset_token={token}" if base else f"?reset_token={token}"


# ── Screens ───────────────────────────────────────────────────────────────────

def _render_reset(token: str) -> None:
    st.title("PM Pilot")
    st.subheader("Set a new password")
    with st.form("reset_form"):
        pw1 = st.text_input("New password", type="password")
        pw2 = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Update password", type="primary")
    if submitted:
        if not pw1 or len(pw1) < 8:
            st.error("Password must be at least 8 characters.")
        elif pw1 != pw2:
            st.error("Passwords do not match.")
        elif auth.reset_password_with_token(token, pw1):
            st.success("Password updated. You can now sign in.")
            st.query_params.clear()
            st.session_state["_reset_done"] = True
        else:
            st.error("This reset link is invalid or has expired. Request a new one.")
    if st.session_state.get("_reset_done") and st.button("Go to sign in"):
        st.session_state.pop("_reset_done", None)
        st.rerun()


def _is_valid_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1] and len(email) >= 5


def _render_login() -> None:
    st.title("PM Pilot")
    st.caption("Sign in to access your projects.")

    tab_labels = ["Sign in", "Forgot password"]
    if config.allow_registration:
        tab_labels.insert(1, "Create account")
    tabs = st.tabs(tab_labels)
    tab_map = dict(zip(tab_labels, tabs))

    with tab_map["Sign in"]:
        with st.form("login_form"):
            identifier = st.text_input("Username or email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary")
        if submitted:
            user = auth.authenticate(identifier, password)
            if user:
                _login(user)
                st.rerun()
            else:
                st.error("Invalid username/email or password.")

    if "Create account" in tab_map:
        with tab_map["Create account"]:
            with st.form("register_form"):
                r_username = st.text_input("Username")
                r_email = st.text_input("Email")
                r_pw1 = st.text_input("Password", type="password")
                r_pw2 = st.text_input("Confirm password", type="password")
                r_submitted = st.form_submit_button("Create account", type="primary")
            if r_submitted:
                if not r_username.strip() or not r_email.strip():
                    st.error("Username and email are required.")
                elif not _is_valid_email(r_email):
                    st.error("Enter a valid email address.")
                elif len(r_pw1) < 8:
                    st.error("Password must be at least 8 characters.")
                elif r_pw1 != r_pw2:
                    st.error("Passwords do not match.")
                else:
                    user, err = auth.register_user(r_username, r_email, r_pw1)
                    if err:
                        st.error(err)
                    else:
                        _login(user)
                        st.rerun()

    with tab_map["Forgot password"]:
        with st.form("forgot_form"):
            email = st.text_input("Account email")
            submitted = st.form_submit_button("Send reset link")
        if submitted:
            result = auth.create_reset_token(email)
            # Always show the same message regardless of whether the account
            # exists, so the form can't be used to probe for valid emails.
            if result:
                user, token = result
                link = _reset_link(token)
                if email_svc.send_reset_email(user.email, link):
                    st.success("If that account exists, a reset link has been emailed.")
                else:
                    # Email not configured (or failed) — show the link directly
                    # so the flow still works in local/dev.
                    st.info("Email isn't configured on this deployment. "
                            "Use this reset link:")
                    st.code(link)
            else:
                st.success("If that account exists, a reset link has been emailed.")


def ensure_authenticated() -> None:
    """Block the app behind a login screen when auth is enabled. Restores a
    prior session from the browser cookie so a page refresh doesn't log the
    user out. No-op when auth is disabled.

    Each script run performs at most ONE cookie operation (read, write, or
    delete) — mixing them in a single run conflicts in the cookie component."""
    if not config.auth_enabled:
        return

    cm = _make_cookie_manager()

    # 1. Pending logout: delete the cookie on this clean pass, then show login.
    if st.session_state.pop("_do_logout", False):
        try:
            cm.delete(_COOKIE_NAME)
        except Exception:
            pass
        _render_login()
        st.stop()

    params = st.query_params
    if "reset_token" in params and not current_user():
        _render_reset(params["reset_token"])
        st.stop()

    # 2. Logged in this session: write the cookie once (on a normal render pass,
    #    not immediately followed by a rerun, so the browser actually stores it).
    if current_user():
        if not st.session_state.get("_cookie_written"):
            _write_session_cookie(cm, current_user()["id"])
            st.session_state["_cookie_written"] = True
        return

    # 3. Not logged in: try to restore from the cookie. On the first run after a
    #    refresh the component may not have returned cookies yet (get_all() is
    #    None) — wait a couple of reruns (the component triggers one when it
    #    loads) before falling back to the login screen.
    cookies = cm.get_all()
    if cookies is None:
        if st.session_state.get("_cookie_wait", 0) < 3:
            st.session_state["_cookie_wait"] = st.session_state.get("_cookie_wait", 0) + 1
            st.stop()
    st.session_state["_cookie_wait"] = 0

    token = (cookies or {}).get(_COOKIE_NAME)
    if token:
        data = crypto.decrypt_json(token)
        uid, exp = data.get("uid"), data.get("exp", 0)
        if uid and exp > time.time():
            user = auth.get_user(uid)
            if user:
                _login(user)
                # Cookie already exists — don't rewrite it next run.
                st.session_state["_cookie_written"] = True
                return

    _render_login()
    st.stop()
