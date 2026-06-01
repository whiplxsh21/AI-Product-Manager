# Sentinel — Feature Deep Dive & Screen Walkthrough

**Date:** April 1, 2026
**Time:** 2:00 PM – 2:54 PM
**Duration:** 54m 41s
**Meeting Type:** Microsoft Teams Recording
**Attendees:**
- Megan O'Donnell — Product Manager
- Sandeep Bhatt — Head of Procurement Analytics
- Yusuf Demir — Director, Supply Chain Risk
- Naomi Kessler — Senior UX Designer (newly assigned)
- Sebastián Vargas — Tech Lead, Backend
- Tobi Lawal — Tech Lead, Frontend

Recording started by Megan O'Donnell

---

Megan O'Donnell  0:02
Recording on. Naomi this is your first session on Sentinel so I'll over-share context. Sandeep and Yusuf are the subject matter experts. Sebastián and Tobi are tech leads. We have fifty-five minutes. Goal today is to walk through the main screens, validate the data needs, and identify any blockers.

Naomi Kessler  0:25
Sounds good. I've read both the brief and the scoring methodology, so I'm caught up on context.

Megan O'Donnell  0:33
Perfect. Let me share my screen with the rough flow I sketched. You can see I have it as five primary screens. Overview Dashboard, Supplier Detail, Alerts Workspace, Reports, and Configuration. Let's go through each.

Megan O'Donnell  0:50
Overview Dashboard is the home page after login. Top of page, a header with the Sentinel logo, search bar in the middle "Search suppliers, categories, countries", and on the right a notifications bell and a user menu. Below the header, a left sidebar with the five sections — Overview, Suppliers, Alerts, Reports, Settings. Sidebar is collapsible.

Naomi Kessler  1:18
Standard pattern, fine.

Megan O'Donnell  1:21
On the Overview itself, top section is what I'm calling the Risk Pulse. Four big cards across the top, like KPI tiles. One — total suppliers being monitored. Two — high-risk supplier count, with a trend arrow. Three — open alerts requiring action. Four — average composite risk score, with a trend.

Yusuf Demir  1:48
The number one and number four are nice-to-haves. The action items are two and three. Hot alerts and high-risk count.

Megan O'Donnell  1:58
Reorder so the action items are most prominent. Got it.

Yusuf Demir  2:03
Also, on high-risk count, that's only useful with a delta — how many added in the last seven days. Adding alone is a vanity number.

Megan O'Donnell  2:14
Delta over seven days as the default, with a toggle to thirty days. Captured.

Megan O'Donnell  2:20
Below the KPI tiles, two main panels. Left is a heat map by category. So twelve rows for our top twelve categories, columns for the five sub-scores, cells colored red yellow green based on risk level. Clicking a cell drills you into the suppliers in that category contributing to that score.

Sandeep Bhatt  2:46
Categories on rows, sub-scores on columns. I like it. But also include a column for composite score on the left of the heat map.

Megan O'Donnell  2:56
Composite first column, then the five sub-scores. Captured.

Megan O'Donnell  3:01
Right panel on the Overview is what I'm calling the World View. A map of supplier locations colored by country risk level. Bubbles sized by spend exposure to that country. Hovering shows the country name and the count of suppliers there.

Yusuf Demir  3:21
That's the crisis-mode visualization. When something happens we click on the country and we see the exposed suppliers.

Megan O'Donnell  3:30
Exactly. Click a country, modal opens with the list. The list is sortable.

Naomi Kessler  3:36
On the map, are we doing real map tiles or a simplified vector outline?

Tobi Lawal  3:42
Simpler vector world map is sufficient. Mapbox or open-source equivalents both work. I'd avoid full tile services for the audit log requirements. Simpler outline is easier to govern.

Megan O'Donnell  3:57
Vector world map, not tile-based. Captured.

Megan O'Donnell  4:01
Below those two panels is what I'm tentatively calling the Top Movers section. Six cards in a row. Each card is a supplier whose composite score changed by more than ten points in the last seven days. Card shows supplier name, current score, change, and a sparkline of the score history.

Yusuf Demir  4:24
Top movers is fantastic for proactive risk management. Plus one from me. Six cards is enough.

Sandeep Bhatt  4:32
Suggest two rows of movers, with deteriorated on top, improved on bottom, six each.

Yusuf Demir  4:40
Good idea. Deterioration is more important visually but improved suppliers also matter because we might unblock something.

Megan O'Donnell  4:50
Two rows, deteriorated and improved. Captured.

Megan O'Donnell  4:54
Bottom of Overview is the Open Alerts strip. A table of currently open alerts, columns are alert title, supplier, severity, age, assigned to, and an action column with View and Acknowledge buttons. Limited to top ten with a "see all" link to the Alerts Workspace.

Yusuf Demir  5:18
The table is good. Add a filter at the top of the strip — show all, mine only, my team's. Toggle pills.

Megan O'Donnell  5:28
Filter toggle pills at top of the alert strip. Captured.

Megan O'Donnell  5:33
Okay Overview done. Next is Supplier Detail. This is reachable from a search result, from a heat map cell, from a top mover card, from an alert. URL is /suppliers/{id}.

Megan O'Donnell  5:48
Top of the page, supplier header. Logo or initials, supplier legal name, country flag and country name, primary category, total annual spend, contract end date. Right side has two CTAs — Open Mitigation Plan and Contact Account Manager.

Naomi Kessler  6:11
Mitigation Plan as a CTA, what does that open?

Megan O'Donnell  6:14
Drawer that slides in from the right. Shows the current mitigation plan if one exists, or a blank template to create one. Mitigation plan has fields — risk type being mitigated, mitigation owner, target date, status, plan steps as a list, alternative suppliers being qualified, last update.

Naomi Kessler  6:38
Drawer pattern is good for this. Keeps you on the supplier page.

Megan O'Donnell  6:42
Below the header, the supplier risk score panel. Big composite score number, color coded. Five sub-scores below it as smaller cards, each with current value, seven-day trend, and an info icon that opens a tooltip explaining how that score is computed.

Sandeep Bhatt  7:03
Tooltip with formula and inputs is critical. Without it, scores feel like a black box.

Megan O'Donnell  7:11
Tooltip with formula, inputs, and last data update timestamp. Captured.

Megan O'Donnell  7:17
Below the score panel, tabs. Tab one is Risk Timeline — chronological feed of risk events for this supplier. Score changes, news items, financial events, mitigation plan updates. Each event has a timestamp and a source.

Yusuf Demir  7:35
Risk Timeline is the key analyst feature. They will spend most of their time here.

Megan O'Donnell  7:42
Tab two is Performance, which shows delivery on-time rate, quality acceptance rate, payment terms, and dispute history.

Sandeep Bhatt  7:53
Performance pulls from SAP. Make sure we surface the source.

Megan O'Donnell  7:58
Source labels under every metric. Captured.

Megan O'Donnell  8:02
Tab three is News & Mentions. Pulls from Bloomberg feed and a couple of supplementary feeds. Filtered to articles mentioning this supplier, with sentiment color-coded.

Yusuf Demir  8:15
Sentiment is sometimes garbage. Especially for technical industry news that's mostly neutral. Make sure the sentiment is a hint not a fact.

Megan O'Donnell  8:25
Sentiment displayed as colored dot with hover that explains the model confidence. Captured.

Megan O'Donnell  8:32
Tab four is Documents. Contracts, audit reports, certifications, ESG attestations. Mostly read-only links to our procurement document store.

Megan O'Donnell  8:43
Tab five is Notes & Conversations. Like a CRM activity feed where category managers and analysts log their interactions with the supplier — calls, emails, meeting notes.

Sandeep Bhatt  8:58
Notes have to be searchable and have to be tagged so we can filter to specific topics later.

Megan O'Donnell  9:05
Tags on notes. Captured.

Megan O'Donnell  9:08
Right sidebar on Supplier Detail has Quick Facts. Country, alternative suppliers we have qualified, sole-source flag, last audit date, contract value. Plus a "People" section listing the assigned category manager and risk analyst.

Naomi Kessler  9:28
Right sidebar is fine but watch the width on smaller laptop screens. Maybe collapse on screens under thirteen hundred.

Megan O'Donnell  9:38
Responsive collapse at thirteen hundred pixels. Captured.

Megan O'Donnell  9:42
Alerts Workspace next. This is the central place for managing alerts.

Megan O'Donnell  9:48
Layout is a master-detail. Left panel is a filterable list of alerts. Right panel is the detail of the selected alert.

Megan O'Donnell  9:58
List panel header has a search bar, filter chips for severity, assignee, status, supplier, alert type. Then a list of alert rows. Each row has severity icon, title, supplier, age, assignee avatar.

Yusuf Demir  10:18
Make age the most prominent visual. An alert that's been open for forty-eight hours is what I want to see immediately.

Megan O'Donnell  10:27
Age in big bold text on each row. Captured.

Megan O'Donnell  10:31
Detail panel shows alert metadata at top — title, severity, type, source, triggered date, current status. Below that, a description and a "Why this fired" panel that explains the trigger condition.

Sandeep Bhatt  10:48
Why this fired panel is essential. If analysts don't know why an alert exists they can't validate it.

Megan O'Donnell  10:56
Below explanation, the affected supplier list. Most alerts will affect one supplier but some, like a country risk spike, can affect many.

Megan O'Donnell  11:08
Below affected suppliers, the response section. Status dropdown — new, acknowledged, in progress, resolved, false positive. Assignee dropdown. Comments thread. Linked mitigation plan if any.

Yusuf Demir  11:25
Comments thread should support @mentions of teammates. We work cross-team a lot.

Megan O'Donnell  11:32
@mentions with Teams notification. Captured.

Megan O'Donnell  11:36
On Reports. This is the smallest screen but important for execs.

Megan O'Donnell  11:42
Reports has three sub-pages. The Weekly Executive Brief — auto-generated PDF and a web view, sent every Monday morning. The Category Health Report — generated on demand for a selected category, downloadable as PDF or PowerPoint. The Audit Log — read-only log of system access and changes for compliance.

Sandeep Bhatt  12:08
PowerPoint export is what executives actually want. Don't skip it.

Megan O'Donnell  12:13
PowerPoint plus PDF for category reports. Captured.

Yusuf Demir  12:19
Audit log needs to be filterable by user, date, action type, and be exportable for compliance reviews.

Megan O'Donnell  12:28
Audit log filters and CSV export. Captured.

Megan O'Donnell  12:32
Settings, briefly. Three sub-pages. Alert Configuration — define new alert rules with conditions and thresholds, schedule, audience. User Management — admin only, control who has access to what categories and what permissions. Data Sources — admin only, control which data sources are enabled and view their sync status.

Sandeep Bhatt  13:00
Alert configuration is the most powerful and most dangerous setting. We need a strict workflow where a draft alert has to be reviewed before going live, otherwise we'll get noise.

Yusuf Demir  13:13
Draft, preview against historical data, review by another admin, activate. Four step.

Sandeep Bhatt  13:21
Preview against historical data is important. Show the alert author what their proposed alert would have fired on for the last ninety days.

Megan O'Donnell  13:31
Alert builder with historical preview, second-admin review before activation. Captured.

Megan O'Donnell  13:38
Tobi from frontend, anything?

Tobi Lawal  13:41
Few things. One, the master-detail pattern in the alerts workspace needs URL-driven state so analysts can share specific alert URLs with each other. Two, the supplier detail is going to be a heavy page, we need to be smart about lazy loading the tabs. Three, the world map is the biggest visual component, I want to use SVG rather than canvas for accessibility.

Megan O'Donnell  14:06
All sensible, captured.

Megan O'Donnell  14:09
Sebastián from backend?

Sebastián Vargas  14:13
The scoring service needs to be its own microservice with a documented API because we're going to expand the inputs over time. Also the alert engine — I propose we keep it rules-based for v1, evaluated every fifteen minutes on a cron. Alert rules are stored as JSON in the database. Eventually we'll move to streaming but not v1.

Megan O'Donnell  14:39
Rules-based fifteen minute evaluation, alert rules as JSON. Captured.

Sebastián Vargas  14:45
On data refresh. SAP daily, D and B weekly, news feed near-real-time but cached for thirty minutes to avoid hammering. Marsh weekly.

Megan O'Donnell  14:58
Locked.

Megan O'Donnell  15:00
Naomi how do you feel about the screen set.

Naomi Kessler  15:04
Five screens is right. The supplier detail is doing a lot of work, which is fine because it's the analyst's workbench. The overview balances overview with action. Alerts workspace is well-structured. Reports and settings are utility but I'll style them carefully so they don't feel like an afterthought. I want to do a working session with you next week to mock the overview and supplier detail in higher fidelity.

Megan O'Donnell  15:32
Books a session for Wednesday afternoon. Done.

Megan O'Donnell  15:36
Actions. Naomi to deliver high fidelity mocks for overview and supplier detail by April 15. Sebastián to write the scoring service API spec by April 10. Tobi to spike the world map component by April 12. Sandeep to review the alert rule schema with me Friday. Yusuf to get me ten realistic alert scenarios for testing by next Wednesday.

Sandeep Bhatt  16:08
Confirmed.

Yusuf Demir  16:10
Confirmed.

Megan O'Donnell  16:12
Anything else from anyone.

Tobi Lawal  16:14
Nothing.

Sebastián Vargas  16:16
Just one thing. Have we made a decision on whether mitigation plans live in Sentinel or in our existing GRC system?

Megan O'Donnell  16:25
Sentinel for now. We can integrate later. Don't want to slow this down.

Sebastián Vargas  16:30
Acknowledged.

Megan O'Donnell  16:32
Recording stopping. Thanks team.

Megan O'Donnell stopped transcription
