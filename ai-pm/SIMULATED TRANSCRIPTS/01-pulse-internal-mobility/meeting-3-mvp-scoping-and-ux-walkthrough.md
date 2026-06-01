# Pulse — MVP Scoping & UX Walkthrough

**Date:** May 6, 2026
**Time:** 11:00 AM – 11:55 AM
**Duration:** 55m 32s
**Meeting Type:** Microsoft Teams Recording
**Attendees:**
- Saurabh Mehta — Product Manager
- Jonas Mueller — Lead Product Designer
- Marcus Webb — Director, Engineering
- Helena Stark — Senior Counsel, Employment Law
- Daniel Osei — IT Director, Workforce Systems
- Tomás Reyes — Staff Engineer (Workday integration spike owner)

Recording started by Saurabh Mehta

---

Saurabh Mehta  0:02
Recording is on. Quick housekeeping. Helena thanks for joining, this is the first time we have legal in the room. Daniel did you share the works council update?

Daniel Osei  0:14
Yes, Karsten responded yesterday. Short version, German works council is supportive in principle but they need to see the data flow diagram before we go live in EMEA. So EMEA rollout is, you know, post-launch by a quarter at minimum. US first.

Saurabh Mehta  0:33
Noted. US launch first, EMEA second. We'll document that as out of scope for v1.

Helena Stark  0:39
And just so I have the context, what is Pulse, in one sentence?

Saurabh Mehta  0:44
Pulse is an internal opportunity platform. Employees find roles, projects, and mentorship inside the company. Managers find internal talent. Replaces the unloved Workday careers page.

Helena Stark  0:58
Okay. And the policy I need to weigh in on today is?

Saurabh Mehta  1:03
A few things. One, defaults around profile visibility. Two, when the current manager learns that a direct report is interested in another role. Three, what data we store about people and their interests, and how long.

Helena Stark  1:21
Good. Let me listen first and then I'll raise specific issues.

Saurabh Mehta  1:26
Perfect. Jonas, let's go through the screens. Tomás, when Jonas finishes a screen, can you call out anything that's a technical concern.

Tomás Reyes  1:36
Will do.

Jonas Mueller  1:38
Sharing my screen. First screen is the discovery feed. This is the landing page after SSO. Top of the page, header with the Pulse wordmark, my profile picture top-right, and a notifications bell with a counter. Below that, a primary search bar that says "What are you looking for? Roles, projects, mentors". Below the search, a horizontal nav bar with five tabs — Feed, Search, My Profile, My Applications, and for managers, a sixth tab called Talent Search.

Saurabh Mehta  2:17
So the nav adapts based on role.

Jonas Mueller  2:20
Yes. If you don't have manager flag in Workday, you don't see Talent Search. Below the nav, the feed itself. Cards in a single column on mobile, two columns on desktop wider screens. Each card is one opportunity. Role cards have a title, team, location, posted date, three relevant skill chips, and two CTAs at the bottom — Express Interest and View Details. Project cards have title, duration, time commitment, sponsor, and a Join Project CTA. Mentorship cards have the mentor name, area of focus, and a Request Intro CTA.

Saurabh Mehta  3:08
Card types are differentiated visually?

Jonas Mueller  3:11
Yes, subtle color accent on the left edge, plus a small type badge in the header. Above the feed there's a filter row — opportunity type, function, location, time commitment for projects. Saved searches show as chips below the filters.

Saurabh Mehta  3:30
Good. Tomás?

Tomás Reyes  3:32
For the feed, the question is, what is the ranking. If we just chronologically sort, the feed becomes useless quickly. If we personalize, we need to know what to personalize on. We have skills from profile, we have past application history, we have manager-stated interests. I would suggest v1 is, blend of recency, skill match, and manual featured promotions for important roles.

Saurabh Mehta  4:02
Featured promotions, meaning a curator can pin a role?

Tomás Reyes  4:06
Yes. Talent acquisition or executive teams can promote roles they want visibility on.

Jonas Mueller  4:13
That gives ops control without the personalization being a black box.

Saurabh Mehta  4:18
Approved.

Jonas Mueller  4:20
Okay next screen. Role detail view. Header with the role title, team, manager name and photo, location, posted date, and at the top right, two CTAs side by side — Express Interest and Formal Apply. Below that, a section with the role description, then a section with what success looks like in the first six months — that's a Reema-driven content requirement. Then required skills, nice-to-have skills, team page link, similar roles section at the bottom.

Saurabh Mehta  5:00
Helena anything on the role detail?

Helena Stark  5:03
The "similar roles" section, where does that data come from?

Tomás Reyes  5:08
We compute it server-side based on skill overlap.

Helena Stark  5:12
Fine. The "manager name and photo" — that's published in our employee directory anyway, so that's fine. The salary range, are we showing it?

Saurabh Mehta  5:23
Yes. In California and Colorado we have to. Let's just show salary band on all roles, it simplifies the implementation and avoids the legal patchwork.

Helena Stark  5:34
Strongly recommended.

Jonas Mueller  5:37
Salary band field added to the design.

Saurabh Mehta  5:40
On Express Interest. The flow is, click the button, modal opens, one-line "why are you interested" prompt, submit. The hiring manager sees you in a soft-interest list on their candidate workspace.

Helena Stark  5:56
What does the soft-interest list contain about the employee, and who sees it?

Saurabh Mehta  6:02
The hiring manager only. Employee name, current role, public skills, the one-line note.

Helena Stark  6:09
And the current manager does not see this.

Saurabh Mehta  6:13
Correct. Not until first conversation between employee and hiring manager. We have a structured workflow that triggers a notification to the current manager when the hiring manager marks "had first conversation".

Helena Stark  6:28
Got it. From an employment law standpoint, the soft interest signal is not an application, so it doesn't trigger formal record-keeping requirements. Fine. The formal apply flow does need full documentation — application date, evaluation criteria, decision rationale. That's a record retention thing.

Tomás Reyes  6:51
We have a retention schedule already from Workday for formal applications. We'll align Pulse to the same.

Helena Stark  6:58
Good.

Saurabh Mehta  7:00
Jonas profile screen.

Jonas Mueller  7:03
My Profile is split into two columns on desktop, single column mobile. Left column, profile basics — photo, current role pulled from Workday read-only, location, tenure. Skills as a chips list with an Add Skills button. Open to Opportunities toggle at the top, with a panel that expands to show granular controls when you toggle it on — open to roles in which functions, open to project work yes/no, open to mentorship yes/no, geographic flexibility.

Right column, application history and saved searches. Each application has a status pill — Submitted, Under Review, In Conversation, Offer, Declined. Saved searches as a list with edit and delete actions.

Saurabh Mehta  8:00
Privacy controls. Where?

Jonas Mueller  8:03
Top of left column, right above Open to Opportunities. A privacy panel with three radio options — Discoverable to All Managers, Discoverable Only When I Apply, Hidden. Default is the middle one.

Helena Stark  8:20
Default is "discoverable only when I apply"?

Jonas Mueller  8:24
Yes.

Helena Stark  8:25
That's the safe default. Recommended.

Aisha — wait Aisha isn't here. Saurabh, on defaults, do we agree on this in writing somewhere with People Ops?

Saurabh Mehta  8:38
We will. Pooja has approved verbally. I will get it in writing this week.

Helena Stark  8:43
Please. Defaults are a thing that get litigated.

Saurabh Mehta  8:47
Tomás technical on profile?

Tomás Reyes  8:51
Profile data has two sources. From Workday — role, location, tenure, manager, work email — read-only, synced every fifteen minutes. From the user — skills, open-to settings, privacy settings, photo if they upload a custom one. Stored in our Pulse database. The skills taxonomy is a managed list, we are going to seed it from a vendor taxonomy and let users propose new skills. I will need a moderation process for proposed skills.

Saurabh Mehta  9:25
Skills moderation. Let's task talent acquisition with that.

Jonas Mueller  9:30
Next screen, application tracker, which is the My Applications tab. Table view on desktop, card view on mobile. Columns are Role, Team, Applied, Status, Last Update. Clicking a row opens an application detail with the timeline — date submitted, date under review, date of first conversation, date of decision. Comments from the hiring manager when there is one.

Saurabh Mehta  10:00
Comments from the hiring manager?

Jonas Mueller  10:03
We discussed this with Reema. Hiring managers can leave structured feedback when declining — "skills not yet a match", "role filled by other candidate", "consider re-applying after X". Employees see this. Builds trust.

Helena Stark  10:20
Structured feedback only, no free text? I want to avoid managers writing something that becomes evidence in a discrimination claim.

Jonas Mueller  10:31
Structured options plus an optional free-text field. We can make the free-text field internal-only and not surface it to the employee.

Helena Stark  10:42
That works. Free text manager-to-manager handoff context, structured codes to the employee.

Saurabh Mehta  10:50
Approved.

Jonas Mueller  10:52
Next screen, search and saved searches. Search bar at top with autocomplete on skills, functions, locations. Filters as a sidebar on the left desktop, drawer on mobile. Results as the same card components as the feed. Save Search button at the top of results, opens a modal — name your search, alert frequency choice instant, daily, weekly, or off.

Saurabh Mehta  11:24
Notifications channels at the saved search level?

Jonas Mueller  11:27
At the user level, in their settings. Email is always on, Teams notification opt-in, in-app always on.

Tomás Reyes  11:36
Teams integration — to be clear, in v1 we will use Microsoft Graph to post adaptive cards to the user's personal Teams chat. We will not have a Pulse Teams app yet. That's v1.5.

Saurabh Mehta  11:50
Acceptable.

Jonas Mueller  11:52
Last screen for now, Manager Talent Search. This is the manager-only tab. Header explains "Find internal candidates who have opted in to be discovered". Search by skills, role title, function, level. Results show only employees who have set their privacy to "Discoverable to All Managers". Each candidate card shows name, current role, tenure, skill chips, and a "Reach Out" CTA that sends an introduction message.

Helena Stark  12:30
Manager can only see employees who have opted in to discoverability.

Jonas Mueller  12:35
Correct. Anyone else, they don't appear in search results at all.

Helena Stark  12:40
Confirmed. That handles the consent concern.

Saurabh Mehta  12:44
On "Reach Out", what's the workflow?

Jonas Mueller  12:48
Manager writes a short note about the role, hits send. Employee gets a notification with the manager's note. Employee can decline politely with a templated response, or accept and start a conversation.

Saurabh Mehta  13:05
Decline templates, that's good design.

Tomás Reyes  13:09
On technical for manager search, we will need to be careful about how this scales. If a manager filters too broadly the result set can be tens of thousands. We will paginate and require at least one filter selection beyond function.

Saurabh Mehta  13:25
Acceptable constraint.

Jonas Mueller  13:28
Then the manager's Candidate Workspace, which is a saved area where they track the people they are talking to. Soft interest list, conversations in progress, formal applicants. Like a lightweight CRM.

Saurabh Mehta  13:43
That's eight screens give or take. Feed, role detail, project detail, profile, application tracker, search, manager talent search, candidate workspace. Anything I'm missing?

Jonas Mueller  13:57
Onboarding. First-time user experience. We need a setup wizard that walks new users through claiming their profile, picking skills, setting opt-in preferences. Three or four screens.

Saurabh Mehta  14:11
Onboarding flow yes. Pin that.

Saurabh Mehta  14:15
Marcus on engineering scope. Tomás's spike, where are we?

Marcus Webb  14:20
Tomás summarize?

Tomás Reyes  14:22
Quick version. Workday HR data API can give us positions, employee profiles, manager hierarchy. Latency is the issue. Their rate limits won't let us pull everyone every fifteen minutes, but a change-feed query, which only pulls deltas since last sync, works at fifteen minute granularity. So position freshness is fifteen minutes, that's acceptable. Employee profile freshness is twelve hours, also acceptable. Manager hierarchy is daily, fine.

Saurabh Mehta  14:55
Search backend?

Tomás Reyes  14:57
Elasticsearch for now, with semantic embeddings layered for "find me roles like this one" queries. We talked about a full semantic search but for v1 keyword plus skill faceting plus a similarity index on top will get us eighty percent of value at twenty percent of effort.

Marcus Webb  15:18
Approved. Push semantic search v1.5.

Saurabh Mehta  15:22
Helena anything else for legal?

Helena Stark  15:26
Three items. One, employee data retention. Profile data — keep while active employee plus six months for re-applications. Application data — formal applications, seven years. Soft interest data, ninety days. Saved searches, until the user deletes them.

Tomás Reyes  15:48
Logging that.

Helena Stark  15:50
Two, audit log. We need an audit log of who saw what data. Especially manager searches. If a manager runs a search and sees a list of people, we need to know that happened, for both internal review and potential investigations.

Tomás Reyes  16:08
Audit log on read operations. Adding to the spec.

Helena Stark  16:13
Three, accessibility. WCAG 2.2 AA at minimum. We do not ship things at this company that aren't accessible.

Jonas Mueller  16:23
That's baked in.

Saurabh Mehta  16:25
Okay, success metrics for v1. Let's lock these. Headline, internal fill rate increase from eighteen to twenty-four percent by end of month six. Secondary, fifty percent of eligible employees complete a profile within ninety days of launch. Tertiary, sixty percent of opted-in managers run at least one talent search in their first month. Application abandonment rate below twenty percent.

Marcus Webb  17:00
Aggressive but reachable.

Saurabh Mehta  17:03
Out of scope, EMEA, career map view, full mentorship matching workflow, Outlook integration, mobile app, manager-to-manager talent trading marketplace.

Helena Stark  17:18
What's manager-to-manager trading?

Saurabh Mehta  17:21
A future thing. Not now.

Helena Stark  17:23
Good, leave it out.

Saurabh Mehta  17:25
Actions. Jonas to wire the eight screens by end of next week. Tomás and I to write the data model spec and Workday integration design. Helena to draft the data retention and consent policy doc. Daniel to schedule the works council deep dive for EMEA. I will brief Pooja on this scope and get formal sign-off Monday.

Saurabh Mehta  17:50
Anything else.

Jonas Mueller  17:53
Nothing.

Helena Stark  17:54
All good.

Marcus Webb  17:56
Nope.

Saurabh Mehta  17:58
Stopping recording. Thanks team.

Saurabh Mehta stopped transcription
