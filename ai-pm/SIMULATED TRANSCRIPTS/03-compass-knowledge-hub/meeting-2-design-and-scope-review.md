# Compass — Design Review & v1 Scope Lock

**Date:** March 12, 2026
**Time:** 10:00 AM – 10:54 AM
**Duration:** 54m 33s
**Meeting Type:** Microsoft Teams Recording
**Attendees:**
- Cara Whitfield — Senior Product Manager
- Asha Pillai — Director, Engineering (CX Platform)
- Kevin Brennan — Senior Manager, Knowledge Management
- Eleni Demetriou — Director, Global Support Operations
- Ravi Subramanian — Staff Engineer
- Lena Brooks — Lead Product Designer

Recording started by Cara Whitfield

---

Cara Whitfield  0:03
Recording is on, transcription too. Quick agenda. I want to walk through the screens Lena and I have drafted, validate them with Eleni and Kevin from the user side, get Asha and Ravi on the technical implications, and lock the v1 scope. Fifty-five minutes.

Lena Brooks  0:21
I'll share my screen.

Cara Whitfield  0:24
Before we dive in, just one update. I did the three agent shadow sessions last week. Two big insights worth sharing. One, agents triage tickets fast — they spend maybe ninety seconds reading the ticket before they start trying to solve. Anything we put in front of them has to be useful in that ninety second window. Two, the side panel in Zendesk is real estate they already use for other things. We are going to fight for that space. Implication, our experience has to be obviously valuable in the first three seconds or they collapse the panel.

Eleni Demetriou  1:05
That matches what I see when I'm on the floor.

Lena Brooks  1:09
Okay sharing. So the primary surface is the Zendesk side panel. The width is three hundred forty pixels. The vertical space depends on screen but assume eight hundred pixels.

Cara Whitfield  1:23
The panel has four primary states. State one, the agent has just opened the ticket. We auto-suggest answers based on the ticket content. State two, the agent searches manually. State three, the agent is viewing a specific answer. State four, the agent is providing feedback or no answer was found.

Lena Brooks  1:48
Let me walk through each. State one, auto-suggest. The top of the panel has a header that says Compass, with a small refresh icon. Below the header, a question reformulation — Compass parses the ticket and shows the agent "I think the customer is asking about: [phrased question]". The agent can edit this if Compass got it wrong.

Eleni Demetriou  2:17
Important. Don't just guess and run. Show what you understood and let them correct.

Cara Whitfield  2:24
Below the reformulation, the answer card. Big block with the answer text, sized to about two to three sentences. Below the answer, an "Open in Sources" link that expands to show the cited articles. Below the answer, two big buttons — "This Answered My Question" and "This Didn't Help". One-click.

Kevin Brennan  2:50
Single click feedback is mandatory. Two-click and we lose the data.

Lena Brooks  2:56
Below the buttons, a secondary section "More options" showing up to three alternative answers with shorter text. Agents can expand each.

Eleni Demetriou  3:08
Three alternates is right. More gets overwhelming.

Lena Brooks  3:12
State two, manual search. Agent clicks the search icon in the header. Search bar appears. Natural language input. Recent searches show as chips below.

Lena Brooks  3:24
When the agent types and submits, results show as answer cards in the same format as state one. So the visual pattern is consistent.

Cara Whitfield  3:34
State three, viewing an answer. Click "Open in Sources" or any source link. A drawer slides over the panel showing the source article in full, with the relevant paragraph highlighted. Citation paragraph is scrolled into view. A "Back" link returns to the answer.

Kevin Brennan  3:55
Highlighting the cited paragraph is the trust feature. Agents need to verify quickly.

Lena Brooks  4:02
State four, feedback or no answer. If the agent hits "This Didn't Help", a small form appears — what was missing, was the answer wrong, was it not specific to this customer. Pre-set options plus a free-text field. Submit routes to Kevin's team.

Kevin Brennan  4:21
Where does that show up on my side?

Cara Whitfield  4:24
That's the knowledge author surface. Let me get to that in a minute.

Lena Brooks  4:28
If no answer is found, the panel shows a friendly message — "I don't have a confident answer for this. Here are some related articles you can review", with a list of three or four loosely-related articles. Plus a button "Save this as a gap" that records the query for the analytics team.

Eleni Demetriou  4:51
Save this as a gap is brilliant. Closes the feedback loop on missing content.

Cara Whitfield  4:57
Okay that's the agent experience inside Zendesk. The other surface is the Compass web app for authors and admins. Let me walk through that.

Lena Brooks  5:08
Compass web app has four main areas — Dashboard, Articles, Drafts and Reviews, and Analytics. Plus Settings for admins.

Lena Brooks  5:20
Dashboard for authors and Kevin's team. At the top, four KPI tiles — articles published, drafts in queue, feedback items needing attention, search queries with no answer in the last seven days.

Cara Whitfield  5:36
Feedback items needing attention should be the most prominent.

Lena Brooks  5:40
Yes, biggest tile. Below the tiles, two panels. Left is recent feedback from agents — a list with the query, the answer that was given, the feedback type, the date, and an action button to triage. Right is a list of trending search queries with no answer — these are the content gaps.

Kevin Brennan  6:04
Trending no-answer queries is exactly what we need. We had no data on this before.

Lena Brooks  6:11
Bottom of the dashboard is a recent activity feed — articles published, drafts submitted, reviews completed.

Lena Brooks  6:19
Articles area. List view by default — table with title, status, last updated, owner, view count, helpful percentage. Filters across the top — status, owner, source, tag.

Cara Whitfield  6:35
Helpful percentage as a column is really useful. Articles with low helpfulness scores need rewriting.

Lena Brooks  6:43
Clicking an article opens the article view. Rich rendering of the content with a sidebar showing metadata — owner, last reviewed, helpful percentage, view count, related articles. Edit button at the top right.

Lena Brooks  6:59
The editor itself is rich text. WYSIWYG. We discussed using a simple markdown editor versus rich text and Kevin pushed for rich text because the contributor pool isn't markdown-friendly.

Kevin Brennan  7:13
Confirmed. Half the experts can't or won't use markdown. Rich text or no contribution.

Lena Brooks  7:20
Editor has a top bar with formatting tools, a sidebar with metadata fields — title, summary, tags, audience, source system if migrated. Save Draft and Submit for Review buttons.

Cara Whitfield  7:36
Drafts and Reviews area. List of drafts pending review, columns are title, author, submitted date, reviewer. Clicking opens a side-by-side diff with the previous version if any, or a fresh draft view if new. Reviewer can approve, request changes, or reject with a reason.

Kevin Brennan  7:58
Reviewers need to be able to leave inline comments not just an overall verdict.

Cara Whitfield  8:04
Inline comments on drafts. Captured.

Lena Brooks  8:08
On the wedge feature you wanted Kevin — quick-capture from Slack. Out of band of the web app, we'd add a Slack bot that detects answer-like messages in support channels, prompts the answerer with "Want to save this as a knowledge entry?", and on confirm creates a draft pre-filled with the message text.

Kevin Brennan  8:32
That's the wedge. The reviewer at my team cleans it up.

Cara Whitfield  8:38
Slack bot with draft auto-creation. Captured. Bonus feature for v1 if we have capacity.

Lena Brooks  8:46
Analytics area. Three sub-pages. Performance Overview — utilization rate over time, helpful percentage over time, no-answer rate over time, average ticket resolution time correlated with Compass usage. Article Performance — per-article metrics. Search Insights — query volume, no-answer queries trending up, top queries.

Eleni Demetriou  9:12
Search Insights is what I'll use most. Showing where the gaps are over time.

Asha Pillai  9:20
Analytics implementation note. We log every search and every feedback event with PII-stripped query text. We can build the analytics on a daily aggregation in Snowflake.

Cara Whitfield  9:35
Daily aggregation for analytics. Real-time only for the live dashboards. Captured.

Lena Brooks  9:42
Settings area for admins. Three sub-pages. User Management — who has author, reviewer, admin roles. Source Configuration — which content sources are indexed. LLM Configuration — which prompts are used, what models, what thresholds for confidence.

Asha Pillai  10:03
LLM configuration is admin-only. The thresholds for the no-confidence fallback are tunable and we will tune them based on data.

Cara Whitfield  10:13
Captured.

Cara Whitfield  10:15
Ravi from engineering, technical reactions.

Ravi Subramanian  10:19
On the Zendesk side panel, I have a question. The auto-suggest based on ticket content — when does that fire? On ticket open? On every comment? We need to be smart about it because the LLM call has cost and latency.

Cara Whitfield  10:36
On ticket open and on customer reply. Not on agent typing.

Ravi Subramanian  10:42
That works. Latency budget for the auto-suggest, what's acceptable?

Cara Whitfield  10:48
Three seconds is the goal. Five is acceptable.

Ravi Subramanian  10:52
Sub-three on a RAG pipeline with retrieval plus LLM, we can hit that with caching and a fast retrieval index. We'll need a streaming UI to show partial results if generation is slow.

Lena Brooks  11:07
Streaming text appearance is fine. Add to spec.

Ravi Subramanian  11:11
On the editor, rich text. We'll use TipTap or similar. We need to support code blocks, images, tables, links, and we need to sanitize HTML on submission.

Cara Whitfield  11:24
TipTap. Captured.

Ravi Subramanian  11:27
On embeddings, fourteen hundred articles, plus some Confluence pages plus some other sources, we'll be at maybe ten thousand chunks. pgvector handles that easily. We index on write and re-index on edit.

Cara Whitfield  11:42
On write index, re-index on edit. Captured.

Ravi Subramanian  11:46
Last technical point. We need to handle the case where the underlying article is updated after the answer was generated. If an agent finds an answer and then the article changes the next day, the answer's citation might become wrong. We need versioning of articles and citations need to point to a specific version.

Cara Whitfield  12:08
Article versioning. Big requirement. Captured. Citations stable across edits.

Asha Pillai  12:15
Add to architecture doc.

Cara Whitfield  12:18
Okay scope lock for v1.

Cara Whitfield  12:21
In scope. Zendesk side panel with auto-suggest, manual search, source viewing, feedback. Compass web app with dashboard, article list, article view, rich text editor, drafts and reviews, analytics across three sub-pages, admin settings. Slack bot for quick capture as a bonus if capacity allows. English only. Agent and author and admin personas.

Cara Whitfield  12:50
Out of scope. Customer self-service portal. Multi-language. Other ticketing tools beyond Zendesk. Native mobile. Tier two content sources beyond Confluence, Salesforce KB, and our internal wiki for v1. Predictive routing based on agent skill. Voice channel integration.

Eleni Demetriou  13:14
Add to out of scope, automated ticket resolution. We are not having the LLM resolve tickets, just suggest answers to agents.

Cara Whitfield  13:24
Automated resolution out of scope. Captured.

Cara Whitfield  13:28
Success metrics. Headline, average ticket resolution time decrease by twenty percent within ninety days of launch. Secondary, escalation rate decrease by fifteen percent. Tertiary, agent utilization of Compass — sixty percent of resolved tickets show evidence of Compass interaction. Author productivity — time to publish a new article reduced from average two weeks to three days.

Rohan said the board wants to see this by October. With this scope I am confident we can release a closed beta to one hundred agents in August and general availability by October.

Asha Pillai  14:08
Engineering timeline aligns with that. Three-month build, one month beta, one month hardening.

Cara Whitfield  14:16
Open questions to track. One, how do we handle articles in non-English languages that exist in Salesforce KB. Are they out of v1 scope by being non-English, or do we exclude them from the index. Two, do we want to give individual agents personalization on top of the system answers. Three, the Slack bot needs a separate legal review on what we can capture from internal channels.

Kevin Brennan  14:46
On question one I would exclude non-English content from the index in v1.

Cara Whitfield  14:53
Captured as a working answer pending team review.

Eleni Demetriou  14:58
On question two, no agent personalization in v1. Same answer to the same question regardless of agent.

Cara Whitfield  15:08
Captured.

Cara Whitfield  15:10
Actions. Lena to finalize high fidelity designs for the four side panel states and the dashboard by next Friday. Ravi to write the RAG architecture doc and citation versioning design. Asha to schedule a security review of the OpenAI data flow. Kevin to identify ten gold-standard ticket-to-answer examples for our evaluation harness. Eleni to nominate fifty agents for the closed beta.

Lena Brooks  15:43
Confirmed.

Ravi Subramanian  15:45
Confirmed.

Kevin Brennan  15:47
Confirmed.

Eleni Demetriou  15:49
Confirmed.

Cara Whitfield  15:51
Alright thanks everyone. Stopping the recording.

Cara Whitfield stopped transcription
