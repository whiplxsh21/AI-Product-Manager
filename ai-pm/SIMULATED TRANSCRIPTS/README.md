# Simulated Discovery Transcripts

Three independent product scenarios. Each subfolder has 2–3 meeting transcripts that, taken together, contain enough context to produce **one** rich PRD + framework JSON + BDD stories + wireframe + UX flow when run through PM Pilot.

For each project, upload **all** transcripts in that subfolder as a single batch in PM Pilot, then fill in a Requirement title / persona / output style in the Input Workspace and click Generate.

| Folder | Project | Meetings | What the PRD should cover |
|---|---|---|---|
| `01-pulse-internal-mobility/` | **Pulse** — Internal opportunity & talent-mobility platform | 3 (Discovery → Research debrief → MVP scoping) | Discovery feed, role / project / mentorship cards, manager talent search, opt-in privacy controls, Teams notifications, application tracker |
| `02-sentinel-supplier-risk/` | **Sentinel** — Supplier risk monitoring & alert platform | 2 (Kickoff → Feature deep-dive) | Risk dashboard with KPIs + heat map + world map, supplier detail with composite + sub-scores + risk timeline, alerts workspace with master-detail + workflow, reports & audit log, alert configuration |
| `03-compass-knowledge-hub/` | **Compass** — AI-powered support knowledge hub | 2 (CX leadership discovery → Design & scope review) | Zendesk side panel (auto-suggest, search, source view, feedback states), Compass web app with dashboard, rich-text article editor, drafts/reviews workflow, analytics |

Each transcript intentionally contains:
- Standard corporate meeting boilerplate (introductions, mute issues, recording-start, agenda check, hard stops, action items)
- Speaker turns in `Name LastName  M:SS` format with timestamps
- Filler ("um", "you know", "basically", "right?") that the cleaning step should strip
- Off-topic chatter and procedural meta-talk
- Cross-references between meetings to test sequential context handling
- Explicit personas, pain points (with severity & evidence), epics, technical constraints, success metrics, out-of-scope items, and open questions — so the Framework JSON has rich grounded content

These are synthetic but written to feel like real Microsoft Teams meeting transcripts so the pipeline is exercised end-to-end the way a customer would actually use it.
