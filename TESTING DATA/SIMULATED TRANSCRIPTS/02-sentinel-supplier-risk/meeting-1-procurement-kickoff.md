# Sentinel — Supplier Risk Platform Kickoff

**Date:** March 18, 2026
**Time:** 9:30 AM – 10:25 AM
**Duration:** 55m 12s
**Meeting Type:** Microsoft Teams Recording
**Attendees:**
- Linnea Karlsson — VP, Procurement
- Yusuf Demir — Director, Supply Chain Risk
- Ana Cordeiro — Senior Director, Operations
- Sandeep Bhatt — Head of Procurement Analytics
- Hiroshi Tanaka — Director, IT Enterprise Data
- Megan O'Donnell — Product Manager (driver)

Recording started by Megan O'Donnell

---

Megan O'Donnell  0:03
Recording is on, transcription too. Welcome everyone. Quick round of introductions just because Hiroshi I don't think you've met Yusuf yet.

Hiroshi Tanaka  0:14
Yeah we haven't.

Yusuf Demir  0:16
Hi Hiroshi. I run the Supply Chain Risk function under Linnea. Been at the company three years, before that I was at Maersk on the logistics side.

Hiroshi Tanaka  0:27
Nice to meet you. I run Enterprise Data which is basically the data platform team. We own Snowflake, the integration tier, and the ERP data pipelines.

Megan O'Donnell  0:38
Perfect. Okay let me set the stage. The purpose of today is to align on the problem and the early thinking around what we're calling Sentinel, the supplier risk platform. We have fifty-five minutes. I want fifteen on the problem context from Linnea and Yusuf, fifteen on current pain from operations and analytics, ten on what success looks like, and the rest on the technical realities and what the next two weeks look like.

Linnea Karlsson  1:09
Sounds good Megan.

Megan O'Donnell  1:11
Linnea, can you walk us through why this is on the roadmap now?

Linnea Karlsson  1:15
Sure. Look, I've been in procurement for twenty-two years. What we have learned in the last twenty-four months is that the old assumption, that supplier disruption is rare and exceptional, is wrong. It's now persistent. We had the Suez Canal blockage in twenty-one, the chip shortage, COVID, the war in Ukraine, the Red Sea attacks last year, and now we have, you know, the Taiwan strait tensions and we're already seeing premiums on certain components. This is the new normal.

Yusuf Demir  1:53
And our internal response has been, frankly, primitive. We have a spreadsheet, two spreadsheets actually, that Ana's team and my team keep, with our top three hundred suppliers and their status. When something happens in the news, my team goes and figures out which suppliers are exposed. It's manual, it's slow, and we miss things.

Ana Cordeiro  2:17
We miss things a lot. The classic case from last fall — when the rare earth export restrictions came out of China, it took us nine days to identify which of our suppliers had upstream exposure. By then our competitors had locked up alternative supply. We paid forty percent premiums for three months because we were late.

Megan O'Donnell  2:42
Forty percent on what scale of spend?

Ana Cordeiro  2:46
That category was about ninety million annual. So we ate roughly nine million in unbudgeted cost because we couldn't move fast.

Linnea Karlsson  2:56
And that's just the cost we can measure. There's also customer impact when we couldn't ship product on time, which has dollars associated but they are downstream and harder to attribute.

Megan O'Donnell  3:10
Got it. So the problem is, we have insufficient visibility into the risk in our supplier base, and when something happens we are too slow to respond.

Yusuf Demir  3:21
That's the headline. I would refine it with a second dimension which is, we are mostly reactive. Even when nothing major has happened in the news, we should be doing ongoing risk monitoring on financial health, on geographic concentration, on dependency on single-source suppliers. We don't do any of that systematically. So when a supplier files chapter eleven we are surprised. When a supplier has, you know, a labor dispute we find out from the supplier on our scheduled call.

Megan O'Donnell  3:55
So both lead indicators and lag indicators are weak.

Yusuf Demir  4:00
Exactly.

Sandeep Bhatt  4:02
Megan if I can jump in from analytics. Yusuf is right but I want to add, the data exists. SAP has supplier master data with country, category, spend, contracts. Our payment systems show us payment history which is a proxy for supplier health. We subscribe to Dun and Bradstreet, which has financial risk scores. We have Bloomberg news feeds. We have Marsh's geopolitical risk index. The data is in many places. What we don't have is a unified view that brings them together with the right weighting and the right alerts.

Linnea Karlsson  4:42
That's the gap. The data exists, the integrated story doesn't.

Megan O'Donnell  4:48
Okay. Before we go further on solution, who is the user. Yusuf can you walk through who would use Sentinel.

Yusuf Demir  4:57
I see three users. One is the category manager. Person who owns a specific category of spend like electronic components or industrial chemicals. They want to know, daily, am I in trouble in my category. Two is the supplier risk analyst. That's my team. They do the deep dive on specific suppliers when something flags. Three is the senior executive. Linnea, Ana, our COO. They want a weekly summary and they want to be able to drill into a specific category if there's an issue.

Linnea Karlsson  5:35
I would add a fourth which is the executive on call when a crisis breaks. When something hits the news the first question is which of our suppliers are exposed and that needs to be a five-minute answer, not a five-day answer.

Megan O'Donnell  5:50
Crisis-mode use. That changes the design.

Linnea Karlsson  5:54
Yes. You need to be able to filter by country, region, commodity, category, in seconds, and get a list of exposed suppliers.

Megan O'Donnell  6:04
Got it. Ana, from operations, what do you need?

Ana Cordeiro  6:09
I need three things. First, I need risk scoring at the supplier level that captures the dimensions we care about. Financial, operational, geographic, geopolitical, and reputational. Second, I need alerts that fire when something material changes — a supplier's financial score deteriorates, news sentiment goes negative, geopolitical risk in their region spikes. Third, I need workflow when an alert fires — assign it to someone, track the response, document the mitigation plan. Otherwise alerts just become noise.

Megan O'Donnell  6:51
Workflow on top of alerts is critical. Got it.

Sandeep Bhatt  6:56
Before we go further on workflow, can we talk about the scoring methodology? The risk score is the most contentious thing. If category managers don't trust the score, they will ignore the tool. We've seen this with Riskmethods.

Megan O'Donnell  7:14
Yes — and we have looked at Riskmethods, Resilinc, Everstream. None of them quite fit.

Yusuf Demir  7:21
They are also expensive. Sentinel would be a build, not a buy, primarily because the existing tools don't combine our internal data — payment history, contract terms, our own scoring of our category strategies — with external data the way we need.

Linnea Karlsson  7:38
The build versus buy debate happened last quarter. We landed on build. ELT approved.

Megan O'Donnell  7:45
Approved, good, so we don't need to relitigate.

Sandeep Bhatt  7:49
On scoring, my proposal is, the composite score is a weighted average of five sub-scores. Each sub-score is computed from specific data sources with documented logic. Category managers can see the sub-scores and the inputs, and they can override the composite in their dashboard if they have insight the system doesn't. The override is logged and reviewed.

Ana Cordeiro  8:18
Logged overrides, that's important. I want governance on the data.

Megan O'Donnell  8:23
Sandeep what are the five sub-scores you'd propose?

Sandeep Bhatt  8:28
Financial health from D and B. Operational performance from our payment and delivery history. Geographic concentration based on supplier locations and country risk. Geopolitical sensitivity based on Marsh data and our news feed. And, this is new, a category criticality score that reflects how easy or hard it would be to replace this supplier for the products they supply us.

Yusuf Demir  9:00
Category criticality is the one nobody else has and that we need most.

Megan O'Donnell  9:05
Captured. Sandeep can you write a one-pager on the scoring methodology and circulate by end of next week?

Sandeep Bhatt  9:13
Yes.

Megan O'Donnell  9:14
Hiroshi from IT, what are the technical realities.

Hiroshi Tanaka  9:18
Good question. Few things. Our Snowflake instance has SAP data already, refreshed daily. That's good. Adding D and B and Marsh as data sources is doable, they offer flat-file delivery and we have an ETL pattern. News feed from Bloomberg, we have the entitlement but the integration is fresh, we'll need to do the work. ETL effort total for v1, I'd guess six to eight weeks for two engineers.

Megan O'Donnell  9:51
Okay.

Hiroshi Tanaka  9:53
On the application side, we don't have a frontend team available. You'd need to either pull from product engineering or contract out. We have a custom React framework with our SSO baked in. Stick to that for security and audit reasons. Looker has been suggested for the dashboard view. I would advise against it. Looker is fine for ad hoc analytics, it's not great for the operational workflow Ana is describing. We will end up building a custom application anyway.

Linnea Karlsson  10:24
That matches what I expected. Megan, what's the engineering ask?

Megan O'Donnell  10:30
I will work with the platform team on staffing. Tentatively I'm thinking three frontend engineers, two backend engineers including Hiroshi's data engineers, one designer, plus me for six months for the initial release.

Linnea Karlsson  10:46
That sounds about right. I will go to bat for that budget.

Megan O'Donnell  10:50
Okay let's talk success metrics. Yusuf you proposed some in the pre-read.

Yusuf Demir  10:55
The headline is, time to identify exposure. Today it's days to weeks. Target is sub-thirty-minutes for major incidents. Second metric, reduction in unbudgeted cost from supplier disruption. Last year that was somewhere around thirty-seven million. Aspirational target year one is twenty percent reduction.

Linnea Karlsson  11:18
Aspirational. I would say target ten percent and stretch twenty.

Yusuf Demir  11:23
Fair. Ten target twenty stretch. Third, percent of high-risk suppliers with documented mitigation plans. Today it's near zero. Target ninety percent within six months of launch.

Megan O'Donnell  11:38
Documented mitigation plans, that ties to the workflow Ana mentioned.

Ana Cordeiro  11:43
Exactly.

Megan O'Donnell  11:45
Fourth metric, user adoption. Category managers logging in weekly, target eighty percent of relevant managers.

Yusuf Demir  11:54
Yes.

Megan O'Donnell  11:55
Okay. Out of scope discussion. What are we explicitly not doing in v1.

Linnea Karlsson  12:01
Predictive modeling beyond what's in the scoring methodology. I don't want a black-box ML model in v1. We need to trust the system and that means we need to understand it.

Megan O'Donnell  12:14
Approved.

Yusuf Demir  12:16
Tier two and tier three supplier visibility. We have decent data on our direct suppliers, we have very weak data on their suppliers. There's a whole conversation about supply chain illumination through tools like Sayari or Altana. Not v1.

Ana Cordeiro  12:36
Mobile app. The users are at their desks. We can have a responsive mobile web for the executive use case but not native apps.

Megan O'Donnell  12:46
Mobile-responsive web for execs, no native apps. Captured.

Sandeep Bhatt  12:51
And not integrating into the supplier-facing portal yet. This is internal use only in v1.

Megan O'Donnell  12:58
Internal only, agreed.

Megan O'Donnell  13:00
Actions. I'll write up the product brief by Friday. Sandeep, scoring methodology one-pager by next Friday. Yusuf, can you give me a prioritized list of the top five user stories you want to validate, by Wednesday?

Yusuf Demir  13:18
Yes.

Megan O'Donnell  13:19
Hiroshi, can you scope the data integration with a rough timeline by end of next week?

Hiroshi Tanaka  13:25
Yes.

Megan O'Donnell  13:27
Ana, can you walk me through your current incident response process so I can map it to the workflow design, sometime next week?

Ana Cordeiro  13:36
Yes I'll set up time.

Megan O'Donnell  13:38
Linnea, can you sponsor a meeting with the COO for sign-off in three weeks?

Linnea Karlsson  13:44
Yes I'll book it.

Megan O'Donnell  13:46
Alright. Two minutes left, anything else.

Yusuf Demir  13:50
One thing. The crisis use case. When something breaks, the first place I go has to be the Sentinel home page and the answer has to be on the screen immediately. Don't make me click three times.

Megan O'Donnell  14:04
Crisis answer above the fold, single click maximum. Loud and clear.

Linnea Karlsson  14:10
That's a good principle for the whole tool.

Megan O'Donnell  14:13
Thanks everyone, super productive. Stopping the recording.

Megan O'Donnell stopped transcription
