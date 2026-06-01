# PM Pilot

PM Pilot is an AI system that automates product management work. Feed it messy discovery meeting transcripts, PDF slide decks, and screenshots — it produces a polished PRD, BDD Gherkin user stories, and a Jira-ready JSON export through a structured LangGraph pipeline.

## Prerequisites

- Python 3.11+
- A free Groq API key — get one at [console.groq.com](https://console.groq.com)

## Quickstart

```bash
cp .env.example .env
# Add your GROQ_API_KEY to .env
./run.sh
```

That's it. The app opens at `http://localhost:8501`.

## Upgrading

| What | How |
|---|---|
| Swap LLM provider | Set `LLM_PROVIDER=openai` (or `anthropic`, `ollama`) and add the corresponding API key in `.env` |
| Use PostgreSQL | Set `DATABASE_URL=postgresql://user:pass@host/dbname` in `.env` |
| Enable human-in-the-loop review | Set `HITL_ENABLED=true` in `.env` — pipeline pauses after framework analysis for approval |
| Enable Jira push (v2) | Set `JIRA_ENABLED=true` and fill Jira credentials in `.env` |

## File Structure

```
ai-pm/
├── app.py                    # Streamlit frontend — all four pages
├── main.py                   # FastAPI REST API
├── config.py                 # All configuration via Pydantic Settings + .env
├── database.py               # SQLAlchemy engine, session, table creation
├── models.py                 # ORM models: Project, Document, PipelineRun, GeneratedOutput
├── schemas.py                # Pydantic v2 request/response schemas
├── storage.py                # File storage adapter (local + S3 stub)
├── llm.py                    # LLM factory — get_llm() and get_vision_llm()
│
├── pipeline/
│   ├── graph.py              # LangGraph StateGraph wiring all nodes
│   ├── state.py              # PipelineState TypedDict
│   ├── prompts.py            # All LLM prompt strings
│   └── nodes/
│       ├── ingestion.py      # Node 1: transcript cleaning + PDF/image extraction
│       ├── framework.py      # Node 2: JTBD + Agile framework JSON via LLM
│       ├── checkpoint.py     # Approval gate (auto v1, HITL v2)
│       ├── prd.py            # Node 3: full PRD markdown generation
│       ├── bdd_stories.py    # Node 4: Gherkin BDD stories (no LLM)
│       └── jira_format.py    # Node 5: Jira-ready JSON export (no LLM)
│
├── services/
│   └── project_service.py   # All business logic shared by FastAPI and Streamlit
│
├── .env.example              # All environment variables documented
├── requirements.txt          # Python dependencies
└── run.sh                    # Single-command startup script
```
