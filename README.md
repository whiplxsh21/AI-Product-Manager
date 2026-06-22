# PM Pilot

PM Pilot is a full-stack AI tool that turns the raw, messy output of product
discovery meetings — long transcripts, slide decks, screenshots, documents — into
a complete set of polished product artifacts. You upload what came out of the
meeting, describe what you want built, and PM Pilot runs a multi-stage AI pipeline
that produces a professional PRD, BDD user stories, a Jira-ready backlog,
clickable wireframes, and a UX flow diagram.

It runs locally with nothing but a free Groq API key, and the same codebase
deploys as a multi-user hosted product (login, organizations, plans, billing
tiers, live Jira sync).

> **Setting it up or hosting it?** See **[SETUP_AND_HOSTING.md](SETUP_AND_HOSTING.md)**
> for a step-by-step guide written for first-time users.

---

## What it does

You give PM Pilot the inputs from a discovery meeting and a short description of
the requirement. It produces, in one run:

1. **PRD** — a complete Product Requirements Document in markdown (executive
   summary, problem statement, goals/non-goals, personas, user journey,
   functional requirements, edge cases, technical considerations, success
   metrics, open questions).
2. **BDD user stories** — Gherkin-style (`Given / When / Then`) scenarios for
   every story, grouped by epic.
3. **Jira export** — a Jira-ready JSON backlog of epics and stories, with
   priorities and story points mapped to Jira's fields. Can be downloaded or
   **pushed straight into a live Jira project**.
4. **Wireframes** — low-fidelity wireframes plus a clickable HTML prototype of
   the proposed UI.
5. **UX flow** — a Mermaid flow diagram of the end-to-end user journey.

Every artifact can be viewed in the app, downloaded as Markdown/JSON, or exported
to **Word (.docx)** and **PDF**.

---

## How it works

PM Pilot is built around a [LangGraph](https://github.com/langchain-ai/langgraph)
pipeline. Each stage is a node; the framework JSON produced in stage 2 is the
single source of truth that every later artifact is generated from.

```
Ingestion → Framework → Checkpoint → PRD → BDD → Jira format → Wireframe → UX flow
```

| Stage | What happens | Uses AI? |
|---|---|---|
| **Ingestion** | Reads every uploaded file, extracts text (PDF/DOCX/PPTX), describes images with a vision model, cleans transcripts, and unifies everything into one clean document. | Yes (vision + optional transcript cleaning) |
| **Framework** | A senior-PM analysis (Jobs-To-Be-Done + Agile) producing structured JSON: core job, problem statement, personas, pain points, epics, user stories, metrics, open questions. | Yes |
| **Checkpoint** | Optional human review gate. Auto-approves unless review is enabled. | No |
| **PRD** | Writes the full PRD markdown from the framework. | Yes |
| **BDD** | Pure transformation of the framework into Gherkin scenarios. | No |
| **Jira format** | Pure transformation into the Jira export JSON schema. | No |
| **Wireframe** | Generates wireframes + a clickable HTML prototype. | Yes |
| **UX flow** | Generates a Mermaid user-flow diagram (rendered via Kroki). | Yes |

### Inputs supported

- **Transcripts / notes:** `.txt`, `.md`
- **Documents:** `.docx`
- **Decks:** `.pdf`, `.pptx`
- **Screenshots / images:** `.png`, `.jpg`, `.jpeg`, `.webp` (described by a vision model)

---

## Features

### Generation
- **Multi-stage AI pipeline** producing 5 distinct artifacts from one run.
- **Per-run configuration** — give each run a title, requirement details (what to
  build), a persona override, and an output style (Plain English, Technical,
  Concise, Detailed).
- **Cached cleaning** — cleaned document text is cached per file and reused across
  runs, so re-running is fast and cheap.

### AI providers (swap with no code changes)
- **Groq** (free, default), **OpenAI**, **Anthropic**, **Google Gemini**, **Ollama** (local).
- **Fallback chain** — if the primary provider is rate-limited or exhausted,
  framework/PRD generation automatically falls back to a configured secondary
  model.
- **Free vs Pro modes** — "Free" uses the open/free provider stack; "Pro" runs
  every task on a premium OpenAI model. A user's plan controls which they can use.
- **Configurable transcript cleaning** — local regex (no LLM calls) or LLM-based.

### Human-in-the-loop
- **Framework review** (HITL) — optionally pause after the analysis stage to
  review and edit the framework before the PRD is written.
- **PRD review** — optionally pause after the PRD so a human can review/edit it
  before the remaining artifacts are generated.

### Jira
- **JSON export** in a schema designed to be pushed directly to Jira.
- **Live push** — create epics and stories in a real Jira project via the Jira
  REST API, with idempotent re-pushes (already-created issues are skipped, never
  duplicated).

### Export
- Download every artifact as Markdown / JSON.
- Convert PRD and BDD stories to **Word (.docx)** and **PDF** (pure-Python, no
  system dependencies).

### Multi-user / hosting (optional)
- **Authentication** — username/password login, "remember me" cookies, and
  password reset by email (via Resend).
- **Organizations** — group users into client tenants.
- **Project sharing** — share a project's deliverables read-only with specific
  users, or with an entire organization.
- **Plans** — `free` and `pro` subscription tiers gate which generation mode a
  user can run.
- **Admin panel** — provision organizations and users, set roles and plans, reset
  passwords, and manage the platform's LLM keys/tiers.
- **Encrypted secrets at rest** — per-user LLM keys and Jira credentials are
  Fernet-encrypted in the database, never stored in plaintext.

### Storage & database (swap with no code changes)
- **Database:** SQLite (zero-config local default) or PostgreSQL (e.g. Neon) via a
  connection string.
- **File storage:** local disk, in-database blobs (recommended for hosting), or
  an S3 stub.

---

## Architecture

The codebase enforces a few hard rules that keep it swappable and maintainable:

- **All LLM calls** go through `llm.py` (`get_main_llms()` / vision factory) — no
  provider library is imported anywhere else.
- **All file I/O** goes through `storage.py` (`get_storage()`).
- **All config** comes from `config.py` (Pydantic settings read from `.env`).
- **The UI never calls AI or storage directly** — everything flows through the
  `services/` layer, which is shared by both the Streamlit UI and the FastAPI API.

```
ai-pm/
├── app.py                 # Streamlit UI (the app users see)
├── main.py                # FastAPI API (same logic, programmatic access)
├── config.py              # All settings, read from .env
├── runtime.py             # Per-run LLM config override (multi-user)
├── crypto.py              # Fernet encryption for secrets at rest
├── database.py            # SQLAlchemy engine/session
├── models.py              # ORM models (users, orgs, projects, runs, outputs, …)
├── schemas.py             # Pydantic request/response shapes
├── llm.py                 # LLM + vision provider factories, fallback logic
├── storage.py             # Local / DB / S3 storage adapters
├── auth_ui.py             # Streamlit login / reset screens
├── pipeline/
│   ├── graph.py           # LangGraph wiring of all nodes
│   ├── state.py           # Pipeline state definition
│   ├── prompts.py         # All LLM prompts (single source)
│   ├── wireframe_render.py# Wireframe → HTML rendering
│   └── nodes/             # ingestion, framework, checkpoint, prd,
│                          #   bdd_stories, jira_format, wireframe, ux_flow
├── services/
│   ├── project_service.py # Core project/pipeline business logic
│   ├── auth_service.py    # Login, registration, password reset
│   ├── admin_service.py   # Org + user provisioning
│   ├── platform_service.py# Platform-owned LLM keys + Free/Pro tiers
│   ├── jira_service.py    # Jira connection + live push
│   ├── export_service.py  # Markdown → Word / PDF
│   └── email_service.py   # Password-reset emails (Resend)
├── integrations/
│   └── jira.py            # Jira REST API client
├── requirements.txt
└── .env.example
```

---

## Quickstart (local)

```bash
cd ai-pm
cp .env.example .env          # then add your free GROQ_API_KEY
pip install -r requirements.txt
streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501). With only a Groq
key set, everything runs: no database setup, no login, no extra services.

For full setup and hosting instructions, see
**[SETUP_AND_HOSTING.md](SETUP_AND_HOSTING.md)**.

---

## Tech stack

- **UI:** Streamlit
- **API:** FastAPI
- **Pipeline:** LangGraph + LangChain
- **LLMs:** Groq · OpenAI · Anthropic · Gemini · Ollama
- **Database:** SQLAlchemy over SQLite / PostgreSQL
- **Auth:** bcrypt password hashing, Fernet-encrypted secrets, cookie sessions
- **Email:** Resend
- **Export:** pandoc (bundled), xhtml2pdf
- **Diagrams:** Mermaid via Kroki
