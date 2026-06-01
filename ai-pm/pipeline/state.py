from typing import TypedDict


class PipelineState(TypedDict):
    project_id: str
    run_id: str
    documents: list[dict]       # Selected Document records (id, filename, file_type, storage_path)
    requirement_title: str      # Requirement title / PRD name
    requirement_details: str    # Instructions: what to build + what kind of PRD
    persona_override: str       # Forced primary persona (empty string if none)
    output_style: str           # Plain English | Technical | Concise | Detailed
    cleaned_content: str        # Output of Node 1 — single unified clean document
    framework: dict             # Output of Node 2 — parsed framework JSON
    approval_status: str        # auto_approved | pending | approved | rejected
    approval_notes: str         # Human reviewer notes (empty string if none)
    prd_markdown: str           # Output of Node 3
    prd_storage_path: str       # Path to saved prd.md
    bdd_storage_path: str       # Path to saved bdd_stories.md
    jira_storage_path: str      # Path to saved jira_export.json
    wireframe_storage_path: str # Path to saved wireframe.svg
    ux_flow_storage_path: str   # Path to saved ux_flow.svg
    current_stage: str
    errors: list[str]
