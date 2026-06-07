import json
import threading
import time

import streamlit as st

from config import config
from database import create_tables
import services.project_service as svc
import services.auth_service as auth
import services.jira_service as jira_svc
from integrations.jira import JiraError
import auth_ui

st.set_page_config(page_title="PM Pilot", layout="wide")


@st.cache_resource
def _bootstrap():
    # Runs once per server process (shared across all sessions/reruns). Without
    # this, create_all() + seed_admin() fired on every page navigation, doing
    # several round trips to the remote DB each time — the main cause of the
    # 3-5s lag between pages.
    create_tables()
    auth.seed_admin()
    return True


_bootstrap()

# Block the app behind a login screen when AUTH_ENABLED is true (no-op locally).
auth_ui.ensure_authenticated()

# ── Helpers ───────────────────────────────────────────────────────────────────

STATUS_COLORS = {
    "idle": "#6b7280",
    "running": "#3b82f6",
    "awaiting_approval": "#f59e0b",
    "complete": "#10b981",
    "failed": "#ef4444",
}

STAGE_COLORS = {
    "pending": "#6b7280",
    "running": "#3b82f6",
    "complete": "#10b981",
    "failed": "#ef4444",
    "awaiting": "#f59e0b",
}

STAGE_LABELS = {
    "ingestion": "Ingestion",
    "framework": "Framework Analysis",
    "checkpoint": "Approval Gate",
    "prd": "PRD Generation",
    "bdd": "BDD Stories",
    "jira_format": "Jira Export",
    "wireframe": "Wireframe Diagram",
    "ux_flow": "UX Flow",
}


def _status_badge(status: str, colors: dict) -> str:
    color = colors.get(status, "#6b7280")
    return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:0.8em;font-weight:600">{status.replace("_", " ").title()}</span>'


def _fmt_date(dt) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%b %d, %Y")


# ── Sidebar Navigation ────────────────────────────────────────────────────────
# Buttons (not a radio) because st.sidebar.radio without a key caches its widget
# value across reruns and clobbers session_state.page set by in-page buttons —
# that was the cause of "every click bounces me to home".

if "page" not in st.session_state:
    st.session_state.page = "Projects"

has_project = bool(st.session_state.get("selected_project_id"))
pages = ["Projects", "New Project"] + (["Project Detail", "View Results"] if has_project else [])
if config.auth_enabled:
    pages.append("Settings")

# If the previously-selected page is no longer reachable (e.g. project deleted),
# fall back to Projects so nothing renders against missing context.
if st.session_state.page not in pages:
    st.session_state.page = "Projects"

st.sidebar.title("PM Pilot")
for _p in pages:
    if st.sidebar.button(
        _p,
        key=f"nav_{_p}",
        use_container_width=True,
        type="primary" if _p == st.session_state.page else "secondary",
    ):
        st.session_state.page = _p
        st.rerun()

# Show context for which project is active
if has_project:
    _selected = svc.get_project(st.session_state.selected_project_id)
    if _selected:
        st.sidebar.caption(f"Project · **{_selected.name}**")

# Signed-in user + logout
_user = auth_ui.current_user()
if _user:
    st.sidebar.divider()
    st.sidebar.caption(f"Signed in as **{_user['username']}**")
    if st.sidebar.button("Log out", key="logout_btn", use_container_width=True):
        auth_ui.logout()
        st.session_state.page = "Projects"
        st.rerun()

page = st.session_state.page


# ── Page: Projects ────────────────────────────────────────────────────────────

if page == "Projects":
    st.title("Your Projects")
    projects = svc.get_all_projects(owner_id=auth_ui.current_owner_id())

    if not projects:
        st.info("No projects yet. Create one to get started.")
    else:
        for project in projects:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    st.markdown(f"**{project.name}**")
                    if project.description:
                        st.caption(project.description)
                with c2:
                    st.markdown(_status_badge(project.status, STATUS_COLORS), unsafe_allow_html=True)
                    st.caption(_fmt_date(project.created_at))
                with c3:
                    if st.button("Open →", key=f"open_{project.id}"):
                        st.session_state.selected_project_id = project.id
                        st.session_state.page = "Project Detail"
                        st.session_state.pop("run_id", None)
                        st.rerun()


# ── Page: New Project ─────────────────────────────────────────────────────────

elif page == "New Project":
    st.title("New Project")
    with st.form("new_project_form"):
        name = st.text_input("Project name *")
        description = st.text_area("Description (optional)")
        submitted = st.form_submit_button("Create Project")

    if submitted:
        if not name.strip():
            st.error("Project name is required.")
        else:
            project = svc.create_project(name.strip(), description.strip() or None,
                                         owner_id=auth_ui.current_owner_id())
            st.session_state.selected_project_id = project.id
            st.session_state.page = "Project Detail"
            st.session_state.pop("run_id", None)
            st.rerun()


# ── Page: Project Detail ──────────────────────────────────────────────────────

elif page == "Project Detail":
    project_id = st.session_state.get("selected_project_id")
    if not project_id:
        st.error("No project selected.")
        st.stop()

    project = svc.get_project(project_id)
    if not project:
        st.error("Project not found.")
        st.stop()
    if not auth_ui.can_access(project):
        st.error("You don't have access to this project.")
        st.stop()

    st.title(project.name)
    st.markdown(_status_badge(project.status, STATUS_COLORS), unsafe_allow_html=True)
    st.divider()

    _FILE_TYPE_COLORS = {
        "transcript": "#6366f1",
        "docx": "#6366f1",
        "pdf": "#f59e0b",
        "pptx": "#f59e0b",
        "image": "#10b981",
    }

    # ── Meeting Materials ───────────────────────────────────────────────────────
    st.subheader("Meeting Materials")

    uploaded_files = st.file_uploader(
        "Upload files",
        type=["txt", "md", "docx", "pdf", "pptx", "png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key=f"uploader_{project_id}",
    )
    if uploaded_files:
        existing_docs = svc.get_documents(project_id)
        existing_names = {d.filename for d in existing_docs}
        new_files = [uf for uf in uploaded_files if uf.name not in existing_names]

        if new_files:
            status_msg = st.empty()
            progress_bar = st.progress(0)
            failed = []

            for i, uf in enumerate(new_files):
                status_msg.info(f"Uploading **{uf.name}** ({i + 1}/{len(new_files)})…")
                try:
                    svc.save_document(project_id, uf.name, uf.read())
                except Exception as e:
                    failed.append((uf.name, str(e)))
                progress_bar.progress((i + 1) / len(new_files))

            progress_bar.empty()
            if failed:
                status_msg.error(f"Failed to save: {', '.join(n for n, _ in failed)}")
                time.sleep(2)
            else:
                status_msg.success(f"{len(new_files)} file(s) uploaded successfully.")
                time.sleep(0.8)

            st.rerun()

    docs = svc.get_documents(project_id)
    if docs:
        for doc in docs:
            dc1, dc2, dc3 = st.columns([3, 1, 1])
            with dc1:
                st.text(doc.filename)
            with dc2:
                st.markdown(_status_badge(doc.file_type, _FILE_TYPE_COLORS),
                            unsafe_allow_html=True)
            with dc3:
                if st.button("🗑", key=f"del_{doc.id}"):
                    svc.delete_document(doc.id)
                    st.rerun()
    else:
        st.caption("No files uploaded yet.")

    st.divider()

    is_busy = project.status in ("running", "awaiting_approval")

    # ── Input Workspace ─────────────────────────────────────────────────────────
    st.subheader("Input Workspace")
    st.caption("Describe the PRD you want from these materials. Each generation is saved below.")

    if not docs:
        st.info("Upload at least one material above to generate a PRD.")
    else:
        with st.form("input_workspace"):
            title = st.text_input("Requirement title *",
                                  placeholder="Example: NPI Milestones Historical View")
            details = st.text_area(
                "Requirement details",
                placeholder="Describe what should be built, who needs it, expected behavior, "
                            "which materials to focus on, and the kind of PRD you want.",
                height=120,
            )
            persona = st.text_input("Persona override (optional)",
                                    placeholder="Example: release manager")
            style = st.selectbox("Output style",
                                 ["Plain English", "Technical", "Concise", "Detailed"])
            doc_labels = {f"{d.filename}  ·  {d.file_type}": d.id for d in docs}
            selected_labels = st.multiselect("Materials to consider",
                                             list(doc_labels.keys()),
                                             default=list(doc_labels.keys()))
            submitted = st.form_submit_button("✦ Generate PRD", type="primary",
                                              disabled=is_busy)

        if submitted:
            if not title.strip():
                st.error("Requirement title is required.")
            elif not selected_labels:
                st.error("Select at least one material.")
            else:
                selected_ids = [doc_labels[l] for l in selected_labels]
                cfg = dict(title=title.strip(),
                           requirement_details=details.strip() or None,
                           persona_override=persona.strip() or None,
                           output_style=style,
                           document_ids=selected_ids,
                           llm_settings=auth_ui.current_llm_settings())

                def _run_in_bg(c=cfg):
                    svc.run_pipeline(project_id, **c)

                threading.Thread(target=_run_in_bg, daemon=True).start()
                time.sleep(0.6)
                st.rerun()

    # ── Active run status ────────────────────────────────────────────────────────
    project = svc.get_project(project_id)
    active_run = svc.get_latest_run(project_id)

    if active_run and project.status in ("running", "awaiting_approval", "failed"):
        st.divider()
        st.subheader("Generation Progress")
        st.caption(f"**{active_run.title or 'Untitled PRD'}**")

        stage_statuses = active_run.stage_statuses or {}
        for stage_key, label in STAGE_LABELS.items():
            status = stage_statuses.get(stage_key, "pending")
            rc1, rc2 = st.columns([3, 2])
            rc1.text(label)
            rc2.markdown(_status_badge(status, STAGE_COLORS), unsafe_allow_html=True)

        if project.status == "running":
            current_label = STAGE_LABELS.get(active_run.current_stage, "Processing")
            st.info(f"⚙ Running: **{current_label}**…")
            time.sleep(2)
            st.rerun()

        elif project.status == "failed":
            st.error(f"Pipeline failed: {active_run.error or 'Unknown error'}")
            st.caption("Adjust your inputs and click Generate PRD to try again.")

        if config.hitl_enabled and project.status == "awaiting_approval":
            st.warning("⏸ Paused — review the framework before generating the PRD")
            framework_output = svc.get_output(project_id, active_run.id, "framework")
            if framework_output:
                st.json(json.loads(framework_output.content))
            notes = st.text_area("Notes or corrections for the PRD writer (optional)",
                                 key="approval_notes")
            approve_col, reject_col = st.columns(2)
            with approve_col:
                if st.button("✓ Approve and Generate PRD", type="primary"):
                    fw = json.loads(framework_output.content) if framework_output else {}
                    svc.approve_run(active_run.id, notes, fw)
                    st.rerun()
            with reject_col:
                if st.button("✗ Reject and Discard"):
                    svc.reject_run(active_run.id, notes)
                    st.rerun()

    # ── Generations history ───────────────────────────────────────────────────────
    runs = svc.get_runs(project_id)
    st.divider()
    st.subheader("Generated PRDs")

    if not runs:
        st.caption("No PRDs generated yet.")
    else:
        hc1, hc2, hc3, hc4, hc5 = st.columns([3, 2, 2, 2, 1])
        hc1.markdown("**Title**")
        hc2.markdown("**Persona**")
        hc3.markdown("**Generated**")
        hc4.markdown("**Status**")
        hc5.markdown("**Open**")

        for r in runs:
            rstatus = svc.run_display_status(r)
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            c1.text(r.title or "Untitled PRD")
            c2.text(r.persona_override or "—")
            c3.text(r.started_at.strftime("%b %d, %H:%M") if r.started_at else "—")
            c4.markdown(_status_badge(rstatus, STATUS_COLORS), unsafe_allow_html=True)
            with c5:
                if rstatus == "complete":
                    if st.button("→", key=f"view_{r.id}"):
                        st.session_state.view_run_id = r.id
                        st.session_state.page = "View Results"
                        st.rerun()


# ── Page: View Results ────────────────────────────────────────────────────────

elif page == "View Results":
    project_id = st.session_state.get("selected_project_id")
    if not project_id:
        st.error("No project selected.")
        st.stop()

    project = svc.get_project(project_id)
    if not project:
        st.error("Project not found.")
        st.stop()
    if not auth_ui.can_access(project):
        st.error("You don't have access to this project.")
        st.stop()

    view_run_id = st.session_state.get("view_run_id")
    run = svc.get_run_status(view_run_id) if view_run_id else None
    if run is None:
        run = svc.get_latest_run(project_id)
    if not run:
        st.info("No pipeline run found for this project.")
        st.stop()

    # Back-button row
    back_col, _ = st.columns([1, 5])
    with back_col:
        if st.button("← Back to project", key="back_to_project", use_container_width=True):
            st.session_state.page = "Project Detail"
            st.rerun()

    st.title(run.title or "Results")

    # ── Generation metadata ──────────────────────────────────────────────────────
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f"**Persona:** {run.persona_override or '—'}")
        st.markdown(f"**Requirement title:** {run.title or '—'}")
        st.markdown(f"**Output style:** {run.output_style or '—'}")
    with m2:
        gen_at = run.completed_at or run.started_at
        st.markdown(f"**Generated at:** {gen_at.strftime('%b %d, %Y %H:%M') if gen_at else '—'}")
        st.markdown(f"**Method:** {run.method or 'AI'}")
    if run.requirement_details:
        with st.expander("Requirement details"):
            st.write(run.requirement_details)

    # ── Regenerate visuals action ───────────────────────────────────────────────
    is_busy = project.status in ("running", "awaiting_approval")
    rc1, rc2 = st.columns([2, 5])
    with rc1:
        if st.button("✦ Regenerate Wireframe + UX Flow",
                     key="regen_visuals",
                     disabled=is_busy,
                     use_container_width=True,
                     type="primary"):
            def _regen_in_bg(rid=run.id, ls=auth_ui.current_llm_settings()):
                svc.regenerate_visuals(rid, llm_settings=ls)

            threading.Thread(target=_regen_in_bg, daemon=True).start()
            time.sleep(0.6)
            st.rerun()
    with rc2:
        st.caption("Re-runs only the wireframe + UX flow nodes against this PRD's "
                   "cached framework JSON — no new framework or PRD generation.")

    # Poll while a regeneration (or any pipeline) is in progress so the new
    # SVGs appear automatically without the user having to refresh.
    if is_busy:
        current_label = STAGE_LABELS.get(run.current_stage, "Processing")
        st.info(f"⚙ Running: **{current_label}**…")
        time.sleep(2)
        st.rerun()

    if project.status == "failed" and run.error:
        st.error(f"Last run failed: {run.error}")

    st.divider()

    prd_output = svc.get_output(project_id, run.id, "prd")
    bdd_output = svc.get_output(project_id, run.id, "bdd")
    jira_output = svc.get_output(project_id, run.id, "jira_format")
    wireframe_output = svc.get_output(project_id, run.id, "wireframe")
    ux_flow_output = svc.get_output(project_id, run.id, "ux_flow")
    framework_output = svc.get_output(project_id, run.id, "framework")
    ingestion_output = svc.get_output(project_id, run.id, "ingestion")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["PRD", "BDD Stories", "Jira Export", "Wireframe", "UX Flow"]
    )

    with tab1:
        if prd_output:
            st.download_button(
                "⬇ Download PRD (.md)",
                data=prd_output.content,
                file_name="prd.md",
                mime="text/markdown",
            )
            st.divider()
            st.markdown(prd_output.content)
        else:
            st.info("PRD not yet generated.")

    with tab2:
        if bdd_output:
            st.download_button(
                "⬇ Download BDD Stories (.md)",
                data=bdd_output.content,
                file_name="bdd_stories.md",
                mime="text/markdown",
            )
            st.divider()
            st.markdown(bdd_output.content)
        else:
            st.info("BDD stories not yet generated.")

    with tab3:
        if jira_output:
            st.download_button(
                "⬇ Download Jira Export (.json)",
                data=jira_output.content,
                file_name="jira_export.json",
                mime="application/json",
            )
            st.divider()
            st.json(json.loads(jira_output.content))
            st.info("Jira push will be available in a future version.")
        else:
            st.info("Jira export not yet generated.")

    with tab4:
        st.caption("Drag the downloaded SVG into a Figma frame, or use File → Import.")
        if wireframe_output:
            st.download_button(
                "⬇ Download Wireframe (.svg)",
                data=wireframe_output.content,
                file_name="wireframe.svg",
                mime="image/svg+xml",
            )
            st.divider()
            st.components.v1.html(wireframe_output.content, height=700, scrolling=True)
        else:
            st.info("Wireframe not yet generated.")

    with tab5:
        st.caption("Drag the downloaded SVG into a Figma frame, or use File → Import.")
        if ux_flow_output:
            st.download_button(
                "⬇ Download UX Flow (.svg)",
                data=ux_flow_output.content,
                file_name="ux_flow.svg",
                mime="image/svg+xml",
            )
            st.divider()
            st.components.v1.html(ux_flow_output.content, height=700, scrolling=True)
        else:
            st.info("UX flow not yet generated.")

    st.divider()

    with st.expander("Raw Framework JSON (Node 2 output)"):
        if framework_output:
            st.json(json.loads(framework_output.content))
        else:
            st.caption("Not available.")

    with st.expander("Cleaned Meeting Document (Node 1 output)"):
        if ingestion_output:
            st.text(ingestion_output.content)
        else:
            st.caption("Not available.")


# ── Page: Settings ──────────────────────────────────────────────────────────

elif page == "Settings":
    st.title("Settings")
    user = auth_ui.current_user()
    if not user:
        st.error("Not signed in.")
        st.stop()

    saved = auth.get_llm_settings(user["id"])
    _PROVIDERS = ["groq", "openai", "anthropic", "gemini", "ollama"]
    _SECRET_FIELDS = ("groq_api_key", "openai_api_key", "anthropic_api_key", "gemini_api_key")

    def _provider_index(value: str) -> int:
        return _PROVIDERS.index(value) if value in _PROVIDERS else 0

    st.subheader("LLM configuration")
    st.caption("Your API keys are encrypted before storage. Leave a key field "
               "blank to keep the one already saved. Blank model fields use the "
               "provider's default model.")

    with st.form("llm_settings_form"):
        st.markdown("**Mode**")
        mode = st.radio(
            "Generation mode",
            ["Free (multi-provider)", "Paid (OpenAI only)"],
            index=1 if saved.get("paid") else 0,
            help="Paid uses OpenAI only (gpt-5.4-mini by default) for every step and "
                 "ignores the free-mode providers below. Free uses the providers/keys below.",
        )
        paid_model = st.text_input(
            "Paid model (OpenAI)",
            value=saved.get("paid_model", "") or "gpt-5.4-mini",
            help="Only used in Paid mode. Default is gpt-5.4-mini — change only if you "
                 "specifically want a different OpenAI model.",
        )

        st.divider()
        st.markdown("**Free-mode providers & models** "
                    "_(ignored when Paid mode is selected)_")
        provider = st.selectbox("Primary provider", _PROVIDERS,
                                index=_provider_index(saved.get("llm_provider", "")))
        llm_model = st.text_input("Primary model", value=saved.get("llm_model", ""),
                                  placeholder="blank = provider default")
        cleaning_mode = st.selectbox(
            "Transcript cleaning", ["local", "llm"],
            index=0 if saved.get("cleaning_mode", "local") == "local" else 1,
            help="local = regex (no LLM calls); llm = clean with the light model",
        )

        with st.expander("Advanced model overrides (optional)"):
            fb_options = ["(none)"] + _PROVIDERS
            fb_cur = saved.get("llm_fallback_provider", "")
            fb_idx = fb_options.index(fb_cur) if fb_cur in fb_options else 0
            fallback_provider = st.selectbox("Fallback provider", fb_options, index=fb_idx)
            fallback_model = st.text_input("Fallback model",
                                           value=saved.get("llm_fallback_model", ""))
            vision_provider = st.selectbox(
                "Vision provider", fb_options,
                index=fb_options.index(saved.get("vision_provider", ""))
                if saved.get("vision_provider", "") in fb_options else 0)
            vision_model = st.text_input("Vision model", value=saved.get("vision_model", ""))
            ingestion_provider = st.selectbox(
                "Ingestion provider", fb_options,
                index=fb_options.index(saved.get("ingestion_provider", ""))
                if saved.get("ingestion_provider", "") in fb_options else 0)
            ingestion_model = st.text_input("Ingestion model",
                                            value=saved.get("ingestion_model", ""))

        st.markdown("**API keys**")
        groq_key = st.text_input("Groq API key", type="password",
                                 placeholder="•••• (saved)" if saved.get("groq_api_key") else "")
        openai_key = st.text_input("OpenAI API key", type="password",
                                   placeholder="•••• (saved)" if saved.get("openai_api_key") else "")
        openai_project = st.text_input("OpenAI project (optional)",
                                       value=saved.get("openai_project", ""))
        anthropic_key = st.text_input("Anthropic API key", type="password",
                                      placeholder="•••• (saved)" if saved.get("anthropic_api_key") else "")
        gemini_key = st.text_input("Gemini API key", type="password",
                                   placeholder="•••• (saved)" if saved.get("gemini_api_key") else "")

        save_clicked = st.form_submit_button("Save LLM settings", type="primary")

    if save_clicked:
        new_settings = dict(saved)  # start from existing so blank secrets persist
        new_settings.update({
            "paid": mode.startswith("Paid"),
            "paid_model": paid_model.strip() or "gpt-5.4-mini",
            "llm_provider": provider,
            "llm_model": llm_model.strip(),
            "cleaning_mode": cleaning_mode,
            "llm_fallback_provider": "" if fallback_provider == "(none)" else fallback_provider,
            "llm_fallback_model": fallback_model.strip(),
            "vision_provider": "" if vision_provider == "(none)" else vision_provider,
            "vision_model": vision_model.strip(),
            "ingestion_provider": "" if ingestion_provider == "(none)" else ingestion_provider,
            "ingestion_model": ingestion_model.strip(),
            "openai_project": openai_project.strip(),
        })
        # Secrets: only overwrite when a new value was typed.
        for field, typed in (
            ("groq_api_key", groq_key),
            ("openai_api_key", openai_key),
            ("anthropic_api_key", anthropic_key),
            ("gemini_api_key", gemini_key),
        ):
            if typed.strip():
                new_settings[field] = typed.strip()

        auth.save_llm_settings(user["id"], new_settings)
        st.session_state.llm_settings = new_settings
        st.success("LLM settings saved.")

    # ── Jira integration ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("Jira integration")
    st.caption(
        "Connect your Jira Cloud site to push generated epics & stories. Your API "
        "token is encrypted before storage. Create a token at "
        "id.atlassian.com → Security → 'Create and manage API tokens'."
    )

    jira_saved = jira_svc.get_settings(user["id"])

    with st.form("jira_settings_form"):
        j_site = st.text_input(
            "Jira site URL", value=jira_saved.get("site_url", ""),
            placeholder="https://yourcompany.atlassian.net",
        )
        j_email = st.text_input("Jira account email", value=jira_saved.get("email", ""))
        j_token = st.text_input(
            "Jira API token", type="password",
            placeholder="•••• (saved)" if jira_saved.get("api_token") else "",
            help="Leave blank to keep the token already saved.",
        )
        jc1, jc2 = st.columns(2)
        with jc1:
            j_save = st.form_submit_button("Save Jira settings", type="primary")
        with jc2:
            j_test = st.form_submit_button("Save & test connection")

    if j_save or j_test:
        if not j_site.strip() or not j_email.strip():
            st.error("Site URL and email are both required.")
        elif not (j_token.strip() or jira_saved.get("api_token")):
            st.error("Enter an API token (none saved yet).")
        else:
            try:
                jira_svc.save_settings(
                    user["id"], site_url=j_site, email=j_email,
                    api_token=j_token or None,
                )
                st.success("Jira settings saved.")
            except JiraError as e:
                st.error(f"Could not save: {e.message}")
                j_test = False
            if j_test:
                try:
                    who = jira_svc.test_connection(user["id"])
                    st.success(
                        f"✓ Connected as {who.get('display_name') or 'unknown user'}"
                        + (f" ({who['email']})" if who.get("email") else "")
                    )
                except JiraError as e:
                    st.error(f"Connection failed: {e.message}")

    if jira_svc.is_configured(user["id"]):
        st.markdown("**Target project**")
        cur_key = jira_svc.get_settings(user["id"]).get("project_key", "")
        if cur_key:
            st.caption(f"Current target project: `{cur_key}`")
        if st.button("Load my Jira projects"):
            try:
                st.session_state.jira_projects = jira_svc.list_projects(user["id"])
                if not st.session_state.jira_projects:
                    st.warning("No projects visible to this account.")
            except JiraError as e:
                st.error(f"Could not load projects: {e.message}")
        projects = st.session_state.get("jira_projects", [])
        if projects:
            labels = [f"{p['name']} ({p['key']})" for p in projects]
            keys = [p["key"] for p in projects]
            idx = keys.index(cur_key) if cur_key in keys else 0
            choice = st.selectbox("Project to push into", labels, index=idx)
            if st.button("Save target project"):
                chosen_key = keys[labels.index(choice)]
                jira_svc.save_project_selection(user["id"], chosen_key)
                st.success(f"Target project set to {chosen_key}.")
    else:
        st.info("Save and test your connection above to pick a target project.")

    st.divider()
    st.subheader("Change password")
    with st.form("change_pw_form"):
        new_pw = st.text_input("New password", type="password")
        confirm_pw = st.text_input("Confirm new password", type="password")
        pw_clicked = st.form_submit_button("Update password")
    if pw_clicked:
        if not new_pw or len(new_pw) < 8:
            st.error("Password must be at least 8 characters.")
        elif new_pw != confirm_pw:
            st.error("Passwords do not match.")
        else:
            auth.set_password(user["id"], new_pw)
            st.success("Password updated.")
