# Pulse — Employee Research Debrief & Persona Workshop

**Date:** April 22, 2026
**Time:** 1:00 PM – 1:52 PM
**Duration:** 52m 04s
**Meeting Type:** Microsoft Teams Recording
**Attendees:**
- Saurabh Mehta — Product Manager
- Aisha Tan — HR Business Partner
- Reema Chakraborty — Head of Talent Acquisition
- Priya Raman — Senior UX Researcher
- Jonas Mueller — Lead Product Designer

Recording started by Saurabh Mehta

---

Saurabh Mehta  0:04
Okay we are recording. Priya, why don't you, you know, drive since you ran the interviews.

Priya Raman  0:11
Sure. Just sharing my screen, one second. Okay can everyone see the synthesis board?

Aisha Tan  0:19
Yes.

Jonas Mueller  0:20
Yep.

Priya Raman  0:21
Great. So just to set context, between the eleventh and the eighteenth I ran nine interviews. Three active job seekers, three passive explorers, and three managers. Each was forty-five minutes. The conversations were really, really rich. I'm going to walk through what I heard, and then we can talk about what it means for the product.

Saurabh Mehta  0:43
Sounds good.

Priya Raman  0:45
Let me start with the active seekers because they were the most clear. The pattern across all three was, they all knew they wanted to move within twelve months. None of them had used the Workday careers page in the last six months. All three were actively browsing LinkedIn, two of them had had at least one interview with an external company in the last quarter.

Reema Chakraborty  1:09
Yeah that tracks.

Priya Raman  1:11
The thing that stood out was, when I asked them, you know, "what would make you not leave", the answer was not "more money", it was "I want to know what's possible". Quote from one of them, this is Anjali in engineering, she said, "I'm not even sure what teams exist outside of mine. I'd love to do something in trust and safety but I have no idea who works on it or how to talk to them". That's a discovery problem, not a job posting problem.

Aisha Tan  1:46
Yes. That maps to something I see all the time. The org chart isn't a discovery tool. People want to understand the landscape before they look at specific roles.

Jonas Mueller  1:56
That's a really interesting framing. Discovery before posting.

Saurabh Mehta  2:00
Let's pin that. Discovery experience as a first-class feature.

Priya Raman  2:05
Yes. Second pattern from the active seekers, all three said the application process needs to feel low-stakes. Workday makes you re-enter all your info, write a cover letter, and there's no signal that anyone is going to look at it. Two of them said they would much rather have, basically, an "express interest" mechanism that flags to the hiring manager that someone with their profile is interested, before committing to a formal application.

Saurabh Mehta  2:35
Like a, like a soft signal.

Priya Raman  2:38
Exactly. A soft signal. Lower friction.

Reema Chakraborty  2:42
We have to be careful about that creating noise on the hiring manager side. If everyone clicks express interest, the signal is meaningless.

Priya Raman  2:51
Agreed. There's a design balance there. Maybe expressing interest requires a one-line note about why you're interested. That's enough friction to make it meaningful.

Jonas Mueller  3:03
I like that. One line, one click, done.

Priya Raman  3:08
Third pattern from active seekers, and this came up unprompted twice, they want to know how their internal application compares to external applicants. They are worried that going internal is, you know, a second-class application path.

Reema Chakraborty  3:25
That's a real policy question. We say we prioritize internal but, honestly, hiring managers don't always.

Aisha Tan  3:33
We need to give the user transparency on, like, where they are in the funnel. Even just "your application is under review" with a date stamp. Right now Workday gives you nothing.

Saurabh Mehta  3:46
Good. So that's status visibility on applications. Noted.

Priya Raman  3:50
Okay moving to passive explorers. These three were really interesting because they don't think of themselves as job seekers. But all of them want growth. One quote from Marcus in finance, "I'm not leaving but if you put something interesting in front of me I'd consider it." Two of them said they would absolutely use a tool that showed them, you know, projects that are tangential to their day job.

Aisha Tan  4:20
The project marketplace concept.

Priya Raman  4:22
Yes. And I want to flag, the appetite for project work was higher than I expected. The story behind it is, people want to learn new skills without changing roles. They want the safety of their current job while expanding their, you know, surface area.

Jonas Mueller  4:39
That's a really different mental model from "apply for a job". That's "subscribe to a sprint".

Priya Raman  4:46
Yes. Two passive explorers also said they would set up alerts for skill keywords like "machine learning" or "international expansion" so they get notified when something matching comes up. That's a, that's a key feature.

Saurabh Mehta  5:02
Saved searches with alerts. Got it.

Priya Raman  5:05
Third pattern from passive explorers, anonymity. All three said they would not enable a public profile that anyone could browse. They were okay with, like, sharing their skills if they actively applied for something, but the idea of a, you know, "internal LinkedIn" where anyone could see who's interested in what — they hated that. Quote, "I don't want my manager seeing I'm interested in a role at three AM on a Tuesday."

Aisha Tan  5:36
This is the privacy default question again.

Priya Raman  5:39
Yes. Defaults need to be private and opt-in for any sharing.

Saurabh Mehta  5:44
Noted. Anything else from the explorer group?

Priya Raman  5:48
The last thing was, they want to understand growth paths. So if I'm a senior engineer, what jobs three years out exist that I could grow toward. There was a desire for a, like, a career map view. That might be too ambitious for v1, just flagging.

Saurabh Mehta  6:06
Park it.

Priya Raman  6:08
Parked. Okay managers. This was the most heterogeneous group. Two of them were hugely enthusiastic. One was, you know, mixed.

Reema Chakraborty  6:18
Who was mixed?

Priya Raman  6:20
A director in a customer success org, I'll keep her name out, but she basically said, the moment I have to officially see that one of my reports is looking, I have a problem on my hands. She was not against internal mobility, she was against the surfacing being too early or too public.

Aisha Tan  6:39
That's the timing question.

Priya Raman  6:41
Yes. And her concrete proposal was, the current manager only finds out when the employee has had a first conversation with the hiring manager. Not at expression of interest, not at application. After first-conversation.

Reema Chakraborty  6:56
I think that's reasonable. The hiring manager talks to the employee, they both decide it's worth pursuing, then there's a structured handoff to the current manager.

Saurabh Mehta  7:06
Let's call that the "structured manager notification" feature. Pin it.

Priya Raman  7:11
The two enthusiastic managers, what they wanted most was, finding talent fast. Both said the current process of going through Reema's team is slow. They want a, basically, a search where they can say "I need a Python engineer with infra experience and at least eighteen months in role", and get a list of, you know, people who match, with their permission to be discovered.

Aisha Tan  7:38
Permission to be discovered is critical phrasing. Defaults again.

Priya Raman  7:44
Yes. Default off. Users opt in to "I'm open to being approached for roles matching X criteria". And the manager can search across only those who have opted in.

Jonas Mueller  7:57
That's a really clean model. Marketplace where supply is opt-in.

Saurabh Mehta  8:02
Yes I love that. Reema what does Talent Acquisition look like in that world?

Reema Chakraborty  8:08
Talent Acquisition becomes a service to managers for the people who haven't opted in, or for, you know, complex roles. We are still in the loop but for the easy matches, the platform handles it. I'm okay with that.

Saurabh Mehta  8:23
Good. Last thing from the manager group?

Priya Raman  8:27
Tooling integration. Both enthusiastic managers said, "I will not log into another system". They want this in Teams, in Outlook, wherever they already are. If I have to remember to go to a Pulse website, I won't.

Jonas Mueller  8:43
Teams plugin and Outlook integration. Big.

Saurabh Mehta  8:46
Daniel will need to chime in on what's feasible there.

Priya Raman  8:50
Okay that's the interview synthesis. Let me show the personas we drafted based on this.

Priya Raman  8:57
Persona one, Anjali the Active Seeker. Senior engineer, four years tenure, ready to move but doesn't know where. Wants discovery, wants low-stakes signaling, wants application transparency.

Persona two, Marcus the Passive Explorer. Mid-level finance manager, happy in role, growth-oriented. Wants skill-based alerts, project marketplace, private exploration.

Persona three, Lin the Hiring Manager. Engineering director, hiring for a senior IC role. Wants fast, filtered search of opt-in candidates, integration with where she works.

Persona four, Karim the Current Manager. Anyone whose direct report is exploring. Wants timely but not premature notification, wants control over the conversation.

Saurabh Mehta  9:49
Four personas, that's manageable. Aisha you good with these?

Aisha Tan  9:53
Yes. I would only push to expand persona three. Hiring managers come in different flavors. The HRBP side, the recruiter side. But for v1 I think we collapse.

Saurabh Mehta  10:06
Agreed.

Jonas Mueller  10:08
Can I jump in on design implications now?

Saurabh Mehta  10:11
Please.

Jonas Mueller  10:13
So based on what I'm hearing, the architecture I'd propose is, the main user-facing experience has three areas. A discovery feed which is the landing experience, more like a, you know, Pinterest of internal opportunities than a search results page. A search and saved searches area which is for users who know what they're looking for. And a profile and applications area, where you manage your own state. For managers, it's a separate area, a talent search and a candidate workspace.

Priya Raman  10:50
The discovery feed framing is really good. It maps to what the explorers want.

Jonas Mueller  10:55
On the feed I'm thinking cards. Each card is an opportunity — a role, a project, a mentorship invitation, even a, you know, "team is hiring next quarter" early signal card. Filters across the top. Notifications icon.

Saurabh Mehta  11:13
Cards with mixed content types in a feed. Yes.

Jonas Mueller  11:17
Then a job or project detail view that's much richer than Workday's. It shows the team, the manager, the day-to-day, the skills, related roles, similar roles, who's posted it. And, importantly, the express interest button, plus the formal apply button.

Reema Chakraborty  11:38
Two CTAs, one soft one hard. I like that.

Jonas Mueller  11:42
Then profile editing. We want this to feel like, you know, two minutes not twenty. Skills as chips. Open to opportunities toggle with granular controls — open to roles in X functions, open to projects, open to mentorship. Privacy controls front and center.

Aisha Tan  12:02
Yes the privacy needs to feel like a default value the user explicitly accepted, not buried in settings.

Jonas Mueller  12:10
Agreed. Then the application tracker. Status visibility, dates, next steps. Then for managers, talent search with filters and the "I'm looking for X" saved searches. Plus a candidate workspace that's like a private list of people they are talking to.

Saurabh Mehta  12:30
Good. Anything else before we move to scope decisions?

Priya Raman  12:34
One more pattern, I forgot to mention. Across both seeker groups, mobile was a strong preference for browsing. They use it on the train, between meetings, at lunch. Application can happen on desktop but discovery and notifications need to be mobile-first.

Saurabh Mehta  12:53
Mobile-first feed, confirmed.

Saurabh Mehta  12:56
Okay scope decisions. We have, what, ten minutes left. The features I see for MVP are, discovery feed, search with saved searches and alerts, job and project detail views, profile and privacy controls, formal application plus express interest, application tracker, manager talent search, Teams notifications. Did I miss anything?

Aisha Tan  13:25
Mentorship matching. Do we cut it?

Saurabh Mehta  13:28
Suggesting cut for v1.

Reema Chakraborty  13:31
I would push back on the cut. Mentorship is what gets passive explorers to sign up. It's the wedge.

Jonas Mueller  13:39
Could we do mentorship as a content type in the feed but not a full matching workflow in v1? You see a "open mentor session with X" card and clicking it sends an email intro. Lightweight.

Aisha Tan  13:54
I think that works as a v1.

Saurabh Mehta  13:56
Good. Mentorship as a lightweight card type, no formal matching workflow.

Saurabh Mehta  14:02
Career map view. Cut for v1.

Priya Raman  14:05
Agreed.

Saurabh Mehta  14:06
Outlook integration. Cut, Teams only for v1.

Reema Chakraborty  14:11
Agreed.

Saurabh Mehta  14:12
Okay actions. I'll write up the synthesis as a doc by Friday. Jonas can you do low-fi sketches of the four main screens — feed, detail, profile, manager search — by next Wednesday for our review?

Jonas Mueller  14:27
Yes.

Saurabh Mehta  14:29
Priya, the policy question on when current managers find out, can you do a quick survey across, like, fifty people to validate the "after first conversation" model?

Priya Raman  14:40
Yes. I'll spin that up this week.

Saurabh Mehta  14:43
Reema, can you draft a one-pager on how Talent Acquisition's role evolves with this platform? I want the TA team to feel like a partner not a casualty.

Reema Chakraborty  14:54
Yes I'll do it.

Saurabh Mehta  14:56
Aisha, can you talk to compliance about the opt-in defaults and any constraints on storing skill and interest data?

Aisha Tan  15:04
Yes.

Saurabh Mehta  15:06
Alright that's a wrap. Thanks team this was super productive.

Jonas Mueller  15:11
Thanks.

Priya Raman  15:12
Bye.

Saurabh Mehta  15:14
Stopping recording.

Saurabh Mehta stopped transcription
