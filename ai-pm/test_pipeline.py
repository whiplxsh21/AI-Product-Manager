import uuid
from database import create_tables, SessionLocal
from models import Project, PipelineRun
from storage import get_storage
import services.project_service as svc

create_tables()

SAMPLE_TRANSCRIPT = """
Sarah Chen: Alright team, let's get started. Today we're talking about our onboarding flow.
The drop-off rate after signup is brutal — we're losing about 60% of users in the first week.

Marcus Lee: Yeah I've been looking at the data. Most of them never complete profile setup.
The form is too long and people just bail. We need to cut it down significantly.

Sarah Chen: Agreed. What if we go progressive? Ask for the minimum at signup, then
collect the rest in context when they actually need it.

Marcus Lee: That could work. We also need to fix the email verification — people
aren't getting the verification email or it's going to spam.

Sarah Chen: That's a technical issue we need to escalate. Okay what about the empty state?
When users first log in they see nothing. There's no guidance on what to do next.

Marcus Lee: We should add a checklist. Something like Notion does — a few key actions
that get you to the aha moment fast.

Sarah Chen: Yes. And we should add tooltips on the main features.
First-time users don't know what half the buttons do.

Marcus Lee: How about in-app walkthroughs? We could use something like Intercom or build it ourselves.

Sarah Chen: Let's not build it ourselves. We have enough to do. Intercom or Appcues.
Budget is a concern though — check what we're already paying for.

Marcus Lee: Will do. I think the priority order is: fix email verification, simplify signup,
add onboarding checklist, then tooltips. Walkthrough is nice-to-have.

Sarah Chen: Agreed. Let's get this into a PRD. We need to ship something by end of quarter.
"""

project = svc.create_project("Onboarding Improvement", "Reduce first-week drop-off")
print(f"Created project: {project.id}")

storage = get_storage()
path = storage.save(project.id, "meeting_transcript.txt", SAMPLE_TRANSCRIPT)
print(f"Saved transcript to: {path}")

db = SessionLocal()
from models import Document
doc = Document(
    id=str(uuid.uuid4()),
    project_id=project.id,
    filename="meeting_transcript.txt",
    file_type="transcript",
    storage_path=path,
)
db.add(doc)
db.commit()
db.close()
print("Document record created")

print("\nRunning pipeline (this will take ~30-60s depending on Groq latency)...\n")
run_id = svc.run_pipeline(project.id)

run = svc.get_run_status(run_id)
print(f"Run status: {run.current_stage}")
print(f"Stage statuses: {run.stage_statuses}")

prd = svc.get_output(project.id, run_id, "prd")
if prd:
    print("\n" + "="*60)
    print("PRD (first 1000 chars):")
    print("="*60)
    print(prd.content[:1000])
else:
    print("PRD not generated — check errors above")

jira = svc.get_output(project.id, run_id, "jira_format")
if jira:
    import json
    jira_data = json.loads(jira.content)
    print("\n" + "="*60)
    print(f"Jira Export: {len(jira_data['epics'])} epics")
    for epic in jira_data["epics"]:
        print(f"  {epic['local_id']}: {epic['summary']} ({len(epic['stories'])} stories)")
    print("="*60)
else:
    print("Jira export not generated")
