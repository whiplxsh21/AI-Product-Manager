import json
import threading
import time

import streamlit as st

from config import config
from database import create_tables
import services.project_service as svc
import services.auth_service as auth
import services.jira_service as jira_svc
import services.export_service as export_svc
import services.admin_service as admin_svc
import services.platform_service as platform_svc
from integrations.jira import JiraError
import auth_ui

st.set_page_config(page_title="PM Pilot", layout="wide")

# Trim Streamlit's large default top padding so page titles sit near the top
# instead of below a big band of empty space.
st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; padding-bottom: 2rem; }
      [data-testid="stHeader"] { height: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


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

# Status colors: brand blue for in-progress, Slate for neutral, semantic
# green/red/amber for done/failed/waiting.
STATUS_COLORS = {
    "idle": "#40586D",              # Slate 500
    "running": "#0672CB",           # Blue 600
    "awaiting_approval": "#f59e0b",
    "complete": "#10b981",
    "failed": "#ef4444",
}

STAGE_COLORS = {
    "pending": "#40586D",           # Slate 500
    "running": "#0672CB",           # Blue 600
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


# Markdown → Word/PDF conversions are cached on the document text so a document
# is converted once, not on every rerun.
@st.cache_data(show_spinner=False)
def _docx_bytes(content: str) -> bytes:
    return export_svc.md_to_docx_bytes(content)


@st.cache_data(show_spinner=False)
def _pdf_bytes(content: str) -> bytes:
    return export_svc.md_to_pdf_bytes(content)


def _doc_download_buttons(content: str, base_name: str, key_prefix: str) -> None:
    """Render Markdown / Word / PDF download buttons for a markdown document.
    Each export format is independent — if one converter fails the others (and
    the page) still work."""
    col_md, col_docx, col_pdf = st.columns(3)
    with col_md:
        st.download_button(
            "⬇ Markdown (.md)", data=content, file_name=f"{base_name}.md",
            mime="text/markdown", key=f"{key_prefix}_md", use_container_width=True,
        )
    with col_docx:
        try:
            st.download_button(
                "⬇ Word (.docx)", data=_docx_bytes(content),
                file_name=f"{base_name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"{key_prefix}_docx", use_container_width=True,
            )
        except Exception as e:  # noqa: BLE001 — keep the page usable
            st.caption(f"Word export unavailable: {e}")
    with col_pdf:
        try:
            st.download_button(
                "⬇ PDF (.pdf)", data=_pdf_bytes(content),
                file_name=f"{base_name}.pdf", mime="application/pdf",
                key=f"{key_prefix}_pdf", use_container_width=True,
            )
        except Exception as e:  # noqa: BLE001
            st.caption(f"PDF export unavailable: {e}")


_LLM_PROVIDERS = ["groq", "openai", "anthropic", "gemini", "ollama"]


def _tier_inputs(label: str, tier: dict, prefix: str) -> dict:
    """Render the editable LLM config for one tier (Free/Pro) and return the
    collected values. Used in the Admin LLM dashboard."""
    st.markdown(f"**{label}**")
    none_opts = ["(none)"] + _LLM_PROVIDERS

    def _idx(opts, val):
        return opts.index(val) if val in opts else 0

    paid = st.checkbox("Use paid OpenAI path (one model for every step)",
                       value=bool(tier.get("paid")), key=f"{prefix}_paid")
    paid_model = st.text_input("Paid model (OpenAI)", value=tier.get("paid_model", ""),
                               key=f"{prefix}_paid_model",
                               help="Used only when the paid path is on. e.g. gpt-5.4-mini")
    provider = st.selectbox("Primary provider", _LLM_PROVIDERS,
                            index=_idx(_LLM_PROVIDERS, tier.get("llm_provider")),
                            key=f"{prefix}_provider")
    model = st.text_input("Primary model (blank = provider default)",
                          value=tier.get("llm_model", ""), key=f"{prefix}_model")
    cleaning = st.selectbox("Transcript cleaning", ["local", "llm"],
                            index=0 if tier.get("cleaning_mode", "local") == "local" else 1,
                            key=f"{prefix}_cleaning",
                            help="local = regex (no LLM calls); llm = clean with the light model")
    with st.expander("Advanced (fallback / vision / ingestion)"):
        fbp = st.selectbox("Fallback provider", none_opts,
                           index=_idx(none_opts, tier.get("llm_fallback_provider", "")),
                           key=f"{prefix}_fbp")
        fbm = st.text_input("Fallback model", value=tier.get("llm_fallback_model", ""),
                            key=f"{prefix}_fbm")
        visp = st.selectbox("Vision provider", none_opts,
                            index=_idx(none_opts, tier.get("vision_provider", "")),
                            key=f"{prefix}_visp")
        vism = st.text_input("Vision model", value=tier.get("vision_model", ""),
                             key=f"{prefix}_vism")
        ingp = st.selectbox("Ingestion provider", none_opts,
                            index=_idx(none_opts, tier.get("ingestion_provider", "")),
                            key=f"{prefix}_ingp")
        ingm = st.text_input("Ingestion model", value=tier.get("ingestion_model", ""),
                             key=f"{prefix}_ingm")
    return {
        "paid": paid,
        "paid_model": paid_model.strip(),
        "llm_provider": provider,
        "llm_model": model.strip(),
        "cleaning_mode": cleaning,
        "llm_fallback_provider": "" if fbp == "(none)" else fbp,
        "llm_fallback_model": fbm.strip(),
        "vision_provider": "" if visp == "(none)" else visp,
        "vision_model": vism.strip(),
        "ingestion_provider": "" if ingp == "(none)" else ingp,
        "ingestion_model": ingm.strip(),
    }


# ── Sidebar Navigation ────────────────────────────────────────────────────────
# Buttons (not a radio) because st.sidebar.radio without a key caches its widget
# value across reruns and clobbers session_state.page set by in-page buttons —
# that was the cause of "every click bounces me to home".

if "page" not in st.session_state:
    st.session_state.page = "Projects"

has_project = bool(st.session_state.get("selected_project_id"))
_selected = svc.get_project(st.session_state.get("selected_project_id")) if has_project else None
pages = ["Projects", "New Project"]
if config.auth_enabled:
    pages.append("Shared with me")
# Owners get the full project workspace; shared viewers see results only.
if _selected is not None:
    if auth_ui.is_owner(_selected):
        pages += ["Project Detail", "View Results"]
    else:
        pages += ["View Results"]
if config.auth_enabled:
    pages.append("Settings")
_nav_user = auth_ui.current_user()
if _nav_user and _nav_user.get("role") == "admin":
    pages.append("Admin")

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


# ── Page: Shared with me ──────────────────────────────────────────────────────

elif page == "Shared with me":
    st.title("Shared with me")
    st.caption("Projects people in your organization have shared with you. "
               "Read-only — you can view and download the deliverables.")

    _me = auth_ui.current_user()
    shared = svc.get_shared_with_me(_me["id"]) if _me else []

    if not shared:
        st.info("Nothing has been shared with you yet.")
    else:
        _owner_names = {u.id: u.username for u in admin_svc.list_users()}
        for project in shared:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    st.markdown(f"**{project.name}**")
                    if project.description:
                        st.caption(project.description)
                with c2:
                    st.caption(f"Owner: {_owner_names.get(project.owner_id, '—')}")
                    st.caption(_fmt_date(project.created_at))
                with c3:
                    if st.button("Open →", key=f"openshared_{project.id}"):
                        st.session_state.selected_project_id = project.id
                        latest = svc.get_latest_run(project.id)
                        st.session_state.view_run_id = latest.id if latest else None
                        st.session_state.page = "View Results"
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
    if not auth_ui.is_owner(project):
        st.error("You don't have access to this project. If it was shared with you, "
                 "open it from **Shared with me**.")
        st.stop()

    st.title(project.name)
    st.markdown(_status_badge(project.status, STATUS_COLORS), unsafe_allow_html=True)

    # ── Share (owner only, within organization) ─────────────────────────────────
    if config.auth_enabled and auth_ui.is_owner(project):
        _shareable = svc.shareable_users(auth_ui.current_owner_id())
        _current_share_ids = set(svc.get_share_user_ids(project_id))
        with st.expander(
            f"🔗 Share this project — deliverables, read-only "
            f"({len(_current_share_ids)} shared)"
        ):
            if not _shareable:
                st.caption("No one else is in your organization yet. Ask your admin to "
                           "add teammates to your organization, then you can share this "
                           "project's deliverables with them.")
            else:
                _share_labels = {f"{u.username} ({u.email})": u.id for u in _shareable}
                _default = [l for l, uid in _share_labels.items() if uid in _current_share_ids]
                _picked = st.multiselect(
                    "Share with people in your organization", list(_share_labels.keys()),
                    default=_default, key=f"share_{project_id}",
                    help="They get read-only access to this project's deliverables "
                         "(PRD, BDD, Jira export, wireframe, UX flow) under their "
                         "'Shared with me' tab. They can't see your source materials "
                         "or edit/run the project.")
                if st.button("Save sharing", key=f"savesh_{project_id}"):
                    svc.set_project_shares(project_id, [_share_labels[l] for l in _picked])
                    st.success("Sharing updated.")
                    st.rerun()

    st.divider()

    _FILE_TYPE_COLORS = {
        "transcript": "#0672CB",    # Blue 600
        "docx": "#1885C3",          # Light Blue 500
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
        allowed_modes = platform_svc.allowed_modes(auth_ui.current_plan())
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
            if len(allowed_modes) > 1:
                mode_choice = st.radio(
                    "Generation mode", ["Free", "Pro"], horizontal=True,
                    help="Pro uses premium paid models for higher-quality output. "
                         "Free uses free models.",
                )
            else:
                mode_choice = "Free"
                st.caption("Generation mode: **Free** — contact your admin to enable Pro.")
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
                mode = mode_choice.lower()
                if mode not in allowed_modes:
                    mode = allowed_modes[0]
                cfg = dict(title=title.strip(),
                           requirement_details=details.strip() or None,
                           persona_override=persona.strip() or None,
                           output_style=style,
                           document_ids=selected_ids,
                           mode=mode)

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
    if not auth_ui.can_view(project):
        st.error("You don't have access to this project.")
        st.stop()

    viewer_is_owner = auth_ui.is_owner(project)

    view_run_id = st.session_state.get("view_run_id")
    run = svc.get_run_status(view_run_id) if view_run_id else None
    if run is None:
        run = svc.get_latest_run(project_id)
    if not run:
        st.info("No pipeline run found for this project.")
        st.stop()

    # Back-button row — owners return to the project; shared viewers to their list.
    back_col, _ = st.columns([1, 5])
    with back_col:
        _back_label = "← Back to project" if viewer_is_owner else "← Back to shared"
        if st.button(_back_label, key="back_to_project", use_container_width=True):
            st.session_state.page = "Project Detail" if viewer_is_owner else "Shared with me"
            st.rerun()

    if not viewer_is_owner:
        st.caption(f"Shared with you · owner-managed · read-only")

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

    # ── Regenerate visuals action (owner only) ──────────────────────────────────
    is_busy = project.status in ("running", "awaiting_approval")
    if viewer_is_owner:
        rc1, rc2 = st.columns([2, 5])
        with rc1:
            if st.button("✦ Regenerate Wireframe + UX Flow",
                         key="regen_visuals",
                         disabled=is_busy,
                         use_container_width=True,
                         type="primary"):
                def _regen_in_bg(rid=run.id):
                    svc.regenerate_visuals(rid)

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
    prototype_output = svc.get_output(project_id, run.id, "wireframe_prototype")
    ux_flow_output = svc.get_output(project_id, run.id, "ux_flow")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["PRD", "BDD Stories", "Jira Export", "Wireframe", "UX Flow"]
    )

    with tab1:
        if prd_output:
            _doc_download_buttons(prd_output.content, "prd", f"prd_{run.id}")
            st.divider()
            st.markdown(prd_output.content)
        else:
            st.info("PRD not yet generated.")

    with tab2:
        if bdd_output:
            _doc_download_buttons(bdd_output.content, "bdd_stories", f"bdd_{run.id}")
            st.divider()
            st.markdown(bdd_output.content)
        else:
            st.info("BDD stories not yet generated.")

    with tab3:
        if not jira_output:
            st.info("Backlog not yet generated.")
        else:
            export = json.loads(jira_output.content)
            epics = export.get("epics", [])
            total_stories = sum(len(e.get("stories", [])) for e in epics)

            # ── Readable backlog preview (what will be created) ────────────────
            st.subheader("Backlog to create")
            st.caption(f"{len(epics)} epics · {total_stories} stories will be created in Jira.")

            for epic in epics:
                with st.container(border=True):
                    st.markdown(f"#### 📦 {epic.get('summary') or 'Untitled epic'}")
                    if epic.get("description"):
                        st.caption(epic["description"])
                    stories = epic.get("stories", [])
                    if not stories:
                        st.caption("_No stories under this epic._")
                    for story in stories:
                        pri = story.get("priority")
                        pts = story.get("story_points")
                        meta = " · ".join(
                            x for x in (
                                f"Priority: {pri}" if pri else "",
                                f"{pts} pts" if pts else "",
                            ) if x
                        )
                        line = f"- **{story.get('summary') or 'Untitled story'}**"
                        if meta:
                            line += f"  \n  _{meta}_"
                        st.markdown(line)

            st.divider()

            # ── Push to Jira (owner only) ─────────────────────────────────────
            st.subheader("Push to Jira")
            if not viewer_is_owner:
                st.caption("Only the project owner can push this backlog to Jira. "
                           "You can download the deliverables above.")
            elif not _user:
                st.info("Sign in to push to Jira.")
            elif not jira_svc.is_configured(_user["id"]):
                st.info("Connect your Jira account in **Settings** to push this "
                        "backlog into Jira.")
            else:
                push_state = jira_svc.get_push_status(run.id)
                if push_state and push_state["state"] == "running":
                    st.info("⏳ Pushing to Jira…")
                    time.sleep(2)
                    st.rerun()
                else:
                    cur_key = jira_svc.get_settings(_user["id"]).get("project_key", "")

                    if st.button("🔄 Load my Jira projects", key=f"loadproj_{run.id}"):
                        try:
                            st.session_state.jira_projects = jira_svc.list_projects(_user["id"])
                            if not st.session_state.jira_projects:
                                st.warning("No projects visible to this account.")
                        except JiraError as e:
                            st.error(f"Could not load projects: {e.message}")

                    jira_projects = st.session_state.get("jira_projects", [])
                    target_key = cur_key
                    if jira_projects:
                        labels = [f"{p['name']} ({p['key']})" for p in jira_projects]
                        keys = [p["key"] for p in jira_projects]
                        idx = keys.index(cur_key) if cur_key in keys else 0
                        choice = st.selectbox("Push into which project?", labels,
                                              index=idx, key=f"projsel_{run.id}")
                        target_key = keys[labels.index(choice)]
                    elif cur_key:
                        st.caption(f"Target project: **{cur_key}** — "
                                   "click *Load my Jira projects* to change it.")

                    if not target_key:
                        st.warning("Load your Jira projects and pick one to push into.")
                    else:
                        if st.button(
                            f"🚀 Push {len(epics)} epics + {total_stories} stories → {target_key}",
                            key=f"push_{run.id}", type="primary",
                        ):
                            if target_key != cur_key:
                                jira_svc.save_project_selection(_user["id"], target_key)
                            jira_svc.start_push(_user["id"], run.id)
                            st.rerun()

                    if push_state and push_state["state"] == "done":
                        st.success(
                            f"Done — {push_state['created']} created, "
                            f"{push_state['skipped']} skipped (already pushed), "
                            f"{push_state['failed']} failed."
                        )
                    elif push_state and push_state["state"] == "error":
                        st.error(f"Push failed: {push_state['error']}")

                records = jira_svc.get_sync_records(run.id)
                if records:
                    st.markdown("**Pushed issues**")
                    st.dataframe(
                        [
                            {
                                "Title": r.local_id,
                                "Type": r.issuetype,
                                "Jira key": r.jira_key or "—",
                                "Status": r.status,
                                "Link": r.jira_url or "",
                                "Notes": r.detail or "",
                            }
                            for r in records
                        ],
                        column_config={"Link": st.column_config.LinkColumn("Link")},
                        hide_index=True,
                        use_container_width=True,
                    )

    with tab4:
        if not wireframe_output:
            st.info("Wireframe not yet generated.")
        else:
            st.caption("Click buttons, tabs, and list rows to walk the flow. Use the "
                       "screen list or Prev/Next on the left to move between screens.")
            dl1, dl2 = st.columns(2)
            with dl1:
                if prototype_output:
                    st.download_button(
                        "⬇ Download interactive prototype (.html)",
                        data=prototype_output.content,
                        file_name="wireframe_prototype.html",
                        mime="text/html",
                        use_container_width=True,
                    )
            with dl2:
                st.download_button(
                    "⬇ Download wireframe (.svg)",
                    data=wireframe_output.content,
                    file_name="wireframe.svg",
                    mime="image/svg+xml",
                    use_container_width=True,
                )
            st.divider()
            if prototype_output:
                st.components.v1.html(prototype_output.content, height=860, scrolling=False)
            else:
                # Older runs generated before the interactive prototype existed —
                # fall back to the static scrolling SVG canvas.
                st.components.v1.html(wireframe_output.content, height=700, scrolling=True)

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


# ── Page: Settings ──────────────────────────────────────────────────────────

elif page == "Settings":
    st.title("Settings")
    user = auth_ui.current_user()
    if not user:
        st.error("Not signed in.")
        st.stop()

    # ── Plan (read-only) ──────────────────────────────────────────────────────
    st.subheader("Your plan")
    plan = (user.get("plan") or "free")
    if plan == "pro":
        st.success("**Pro** — you can generate in both Free and Pro modes.")
    else:
        st.info("**Free** — you can generate in Free mode. Contact your admin to "
                "enable Pro.")
    st.caption("Generation models and API keys are managed by your platform admin. "
               "Pick Free or Pro per generation in the project's Input Workspace.")

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


# ── Page: Admin ───────────────────────────────────────────────────────────────

elif page == "Admin":
    admin_user = auth_ui.current_user()
    if not admin_user or admin_user.get("role") != "admin":
        st.error("Admin access required.")
        st.stop()

    st.title("Admin")
    st.caption("Provision client organizations and user accounts. Self-service "
               "signup is disabled — accounts are created here.")

    orgs = admin_svc.list_organizations()
    org_names = {o.id: o.name for o in orgs}
    org_counts = admin_svc.user_counts_by_org()
    _NO_ORG = "(no org)"

    def _org_id_from_label(label: str) -> str | None:
        return None if label == _NO_ORG else next((o.id for o in orgs if o.name == label), None)

    tab_orgs, tab_users, tab_llm = st.tabs(["Organizations", "Users", "LLM & Tiers"])

    # ── Organizations ─────────────────────────────────────────────────────────
    with tab_orgs:
        st.subheader("Organizations")
        if orgs:
            for o in orgs:
                oc1, oc2, oc3 = st.columns([3, 2, 2])
                oc1.markdown(f"**{o.name}**")
                oc2.caption(f"{org_counts.get(o.id, 0)} user(s)")
                oc3.caption(_fmt_date(o.created_at))
        else:
            st.caption("No organizations yet.")

        with st.form("new_org_form"):
            org_name = st.text_input("New organization name")
            if st.form_submit_button("Create organization", type="primary"):
                _, err = admin_svc.create_organization(org_name)
                if err:
                    st.error(err)
                else:
                    st.success("Organization created.")
                    st.rerun()

    # ── Users ───────────────────────────────────────────────────────────────────
    with tab_users:
        st.subheader("Provision a user")
        with st.form("new_user_form"):
            nu_name = st.text_input("Username")
            nu_email = st.text_input("Email")
            nu_pw = st.text_input("Temporary password", type="password",
                                  help="At least 8 characters. Share it with the user; "
                                       "they can change it in Settings.")
            nf1, nf2, nf3 = st.columns(3)
            with nf1:
                nu_org = st.selectbox("Organization", [_NO_ORG] + [o.name for o in orgs])
            with nf2:
                nu_plan = st.selectbox("Plan", ["free", "pro"])
            with nf3:
                nu_role = st.selectbox("Role", ["user", "admin"])
            if st.form_submit_button("Create user", type="primary"):
                _, err = admin_svc.provision_user(
                    nu_name, nu_email, nu_pw,
                    org_id=_org_id_from_label(nu_org), plan=nu_plan, role=nu_role,
                )
                if err:
                    st.error(err)
                else:
                    st.success(f"User “{nu_name.strip()}” created.")
                    st.rerun()

        st.divider()
        st.subheader("Users")
        users = admin_svc.list_users()
        if not users:
            st.caption("No users yet.")
        for u in users:
            with st.container(border=True):
                uc1, uc2, uc3 = st.columns([3, 3, 2])
                uc1.markdown(f"**{u.username}**")
                uc2.caption(u.email)
                uc3.caption("Admin" if u.role == "admin"
                            else org_names.get(u.org_id, _NO_ORG))

                org_opts = [_NO_ORG] + [o.name for o in orgs]
                cur_org_label = org_names.get(u.org_id, _NO_ORG)
                ec1, ec2, ec3, ec4 = st.columns([2, 2, 2, 1])
                with ec1:
                    new_org = st.selectbox(
                        "Org", org_opts,
                        index=org_opts.index(cur_org_label) if cur_org_label in org_opts else 0,
                        key=f"org_{u.id}")
                with ec2:
                    new_plan = st.selectbox("Plan", ["free", "pro"],
                                            index=1 if u.plan == "pro" else 0,
                                            key=f"plan_{u.id}")
                with ec3:
                    new_role = st.selectbox("Role", ["user", "admin"],
                                            index=1 if u.role == "admin" else 0,
                                            key=f"role_{u.id}")
                with ec4:
                    st.write("")
                    if st.button("Save", key=f"save_{u.id}", use_container_width=True):
                        admin_svc.set_user_org(u.id, _org_id_from_label(new_org))
                        admin_svc.set_user_plan(u.id, new_plan)
                        admin_svc.set_user_role(u.id, new_role)
                        st.success(f"Updated {u.username}.")
                        st.rerun()

                with st.expander("Reset password / delete"):
                    rp = st.text_input("New password", type="password", key=f"pw_{u.id}")
                    rc1, rc2 = st.columns(2)
                    with rc1:
                        if st.button("Set password", key=f"setpw_{u.id}",
                                     use_container_width=True):
                            if len(rp) < 8:
                                st.error("Password must be at least 8 characters.")
                            else:
                                admin_svc.reset_user_password(u.id, rp)
                                st.success("Password updated.")
                    with rc2:
                        if st.button("Delete user", key=f"del_{u.id}",
                                     use_container_width=True):
                            if u.id == admin_user["id"]:
                                st.error("You can't delete your own account.")
                            else:
                                n = admin_svc.project_count_for_user(u.id)
                                admin_svc.delete_user(u.id)
                                st.success(f"Deleted {u.username}"
                                           + (f" and {n} project(s)." if n else "."))
                                st.rerun()

    # ── LLM & Tiers ─────────────────────────────────────────────────────────────
    with tab_llm:
        pcfg = platform_svc.get_config()
        pkeys = pcfg["keys"]
        st.subheader("Platform API keys")
        st.caption("Shared provider keys used by every generation, encrypted at rest. "
                   "Leave a field blank to keep the saved key. A blank key falls back "
                   "to the deploy's .env key if one is set.")

        with st.form("platform_llm_form"):
            groq_key = st.text_input("Groq API key", type="password",
                                     placeholder="•••• (saved)" if pkeys.get("groq_api_key") else "")
            openai_key = st.text_input("OpenAI API key", type="password",
                                       placeholder="•••• (saved)" if pkeys.get("openai_api_key") else "")
            openai_project = st.text_input("OpenAI project (optional)",
                                           value=pkeys.get("openai_project", ""))
            anthropic_key = st.text_input("Anthropic API key", type="password",
                                          placeholder="•••• (saved)" if pkeys.get("anthropic_api_key") else "")
            gemini_key = st.text_input("Gemini API key", type="password",
                                       placeholder="•••• (saved)" if pkeys.get("gemini_api_key") else "")

            st.divider()
            st.markdown("### Tier definitions")
            st.caption("What each generation mode uses. Free is the default tier; "
                       "Pro is available to users on the Pro plan.")
            free_vals = _tier_inputs("Free tier", pcfg["free"], "free")
            st.divider()
            pro_vals = _tier_inputs("Pro tier", pcfg["pro"], "pro")

            saved_platform = st.form_submit_button("Save platform LLM settings",
                                                   type="primary")

        if saved_platform:
            new_keys = dict(pkeys)
            for field, typed in (
                ("groq_api_key", groq_key),
                ("openai_api_key", openai_key),
                ("anthropic_api_key", anthropic_key),
                ("gemini_api_key", gemini_key),
            ):
                if typed.strip():
                    new_keys[field] = typed.strip()
            new_keys["openai_project"] = openai_project.strip()
            platform_svc.save_config(new_keys, free_vals, pro_vals)
            st.success("Platform LLM settings saved.")
            st.rerun()
