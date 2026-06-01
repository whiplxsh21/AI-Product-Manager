# Pulse — Internal Mobility Discovery Kickoff

**Date:** April 8, 2026
**Time:** 10:00 AM – 10:48 AM
**Duration:** 48m 12s
**Meeting Type:** Microsoft Teams Recording
**Attendees:**
- Pooja Iyer — VP, People Operations
- Marcus Webb — Director, Engineering
- Reema Chakraborty — Head of Talent Acquisition
- Daniel Osei — IT Director, Workforce Systems
- Aisha Tan — HR Business Partner, Product Org
- Saurabh Mehta — Product Manager (note-taker)

Recording started by Saurabh Mehta

---

Saurabh Mehta  0:02
Okay so the recording is on. Pooja can you confirm you can see the agenda I shared?

Pooja Iyer  0:08
Yeah I can see it. Sorry I was just on another call, let me close my Outlook. Okay go ahead.

Saurabh Mehta  0:18
Cool. Um, so the goal today, like I mentioned in the invite, is to do a, you know, a fairly open discovery on what we are calling, tentatively, the internal mobility platform. Code-name is Pulse. We have about forty-five minutes. I want to leave the last ten for actions and next steps.

Marcus Webb  0:38
Just to flag, I have a hard stop at ten forty-five, my eng leads sync.

Saurabh Mehta  0:43
Noted. Aisha is joining late, she had a one-on-one bleed over. Okay, let me, let me kick off. So Pooja the ask originally came from your org. Can you, can you share the context for everyone? Marcus is new to this.

Pooja Iyer  1:01
Yeah of course. Marcus, basically, what we have been seeing in the last, I would say four quarters, is, regrettable attrition is running at fourteen percent, which is up from like nine percent two years ago. And when we do exit interviews, the top reason, by a pretty wide margin, is "I didn't see a path forward internally". Basically people are leaving because they think they have to leave to grow. Which is, frankly, embarrassing because we have, you know, thousands of open roles internally at any given time.

Marcus Webb  1:38
Hmm. And what's the current state for someone who wants to see those roles?

Pooja Iyer  1:44
So today it's Workday. We have an internal careers page in Workday. And if you ask any employee they will tell you it is, um, it's not great.

Reema Chakraborty  1:55
Can I jump in there? It's bad. I will just say it. The Workday internal careers page, the search is keyword-only, the filters don't work properly, half the listings are stale, and there's no notification when something matching your interests gets posted. People don't trust it. The data we have is engagement is something like, four percent of employees have logged into it in the last twelve months. Four percent.

Marcus Webb  2:23
Wow. Okay.

Saurabh Mehta  2:25
And on the manager side?

Reema Chakraborty  2:28
On the manager side it's worse because managers don't even know it exists for the most part. When they want to fill a role, they go to me, or they go to LinkedIn first. The idea that they could find someone already inside the company, with a known performance record, with context — it just doesn't enter their mind because the system is opaque.

Pooja Iyer  2:51
Right. And there's also a cultural piece. Some managers actively don't want to surface their direct reports as available for other roles, because they don't want to lose them. Which, again, drives the same person to go look externally.

Daniel Osei  3:08
Sorry I muted myself for a moment. Daniel here. From an IT standpoint, I just want to set expectations. Workday is not going away. Whatever we build has to coexist with Workday as the system of record for positions and employee data. So I'm thinking of this as more of a, an experience layer that sits on top.

Saurabh Mehta  3:30
Yes that's exactly the framing I was going to suggest. We are not replacing Workday. We are building, you know, a much better front door to internal opportunities, that pulls from Workday and also adds things Workday doesn't have.

Marcus Webb  3:46
Like what?

Saurabh Mehta  3:48
Like short-term projects. Stretch assignments. Mentorship. The things that aren't formal job postings but are real ways people grow.

Pooja Iyer  4:00
Yeah, the gig marketplace concept. Gloat does this, Fuel50 does this. We have looked at both. They are expensive and they want to own the whole experience including the data, and our security team won't let us send Workday data to them in the way they want.

Daniel Osei  4:18
Confirmed. Legal has already pushed back on the Gloat conversation twice. So a build is more viable than a buy at this point, especially since we have the engineering capacity now after the platform team reorg.

Marcus Webb  4:32
That's a good segue. Saurabh did you see the doc Pooja sent on Monday about budget and headcount?

Saurabh Mehta  4:38
I did. I think we have, what, two engineers, one designer, one PM, which is me, for six months for MVP?

Pooja Iyer  4:48
That's the ask. Not approved yet, going to ELT next Thursday. Today's conversation is partly to make sure we have a sharp story for that meeting.

Saurabh Mehta  4:58
Got it. Okay so let me, let me try to summarize what I'm hearing as the problem we want to solve. And push back if I'm off. We have a workforce of, what, eleven thousand people. Most of them don't know what opportunities exist internally. The system we have is unusable. Managers also don't think internal first. Result, fourteen percent regrettable attrition, costing us, Reema what was the number?

Reema Chakraborty  5:26
Average cost to backfill an engineer is roughly one hundred twenty thousand dollars when you count recruiter fees, ramp time, and the productivity gap. Across the org we estimated the cost of the gap last year at around forty million.

Marcus Webb  5:42
Forty million.

Reema Chakraborty  5:43
Forty.

Marcus Webb  5:45
Okay.

Saurabh Mehta  5:46
So that's the problem. The solution direction is, build a modern internal opportunity platform that, one, makes it dead simple for employees to find roles, projects, and growth opportunities. Two, gives managers a much better way to discover internal talent. Three, integrates with Workday but doesn't try to be Workday. Reasonable so far?

Pooja Iyer  6:09
Yes. I would add a fourth which is, gives People Ops actual data on internal mobility we currently don't have. Right now I cannot tell you, you know, how many cross-org moves happened last quarter, broken down by level or function. We pull it manually with reports.

Daniel Osei  6:28
That's a real gap.

Saurabh Mehta  6:30
Okay. Noted. So let's, let's go deeper on who the users are. Reema you talk to candidates all day. If we are building this for, let's say, an individual contributor in engineering or design or marketing, what does their day-to-day actually look like with this thing?

Reema Chakraborty  6:51
I think the personas split into a few groups. There's the active job seeker, who has decided they want to move and is actively looking. There's the passive explorer, who is happy in their role but curious about what's out there, especially around growth. And there's the project-seeker, who isn't trying to change jobs but wants to do a stretch project for visibility or skill-building. Different needs.

Aisha Tan  7:17
Hi everyone, sorry I'm late, just dropped off the call.

Saurabh Mehta  7:21
Hi Aisha. We're talking through user personas. Reema just laid out three groups, active seeker, passive explorer, project seeker. From your side working with the product org, what would you add?

Aisha Tan  7:34
I would add a fourth which is the returner. People coming back from leave, or coming back from a sabbatical, or who just changed life circumstances and want to look around. They are a sensitive group because they often don't want to broadcast that they are looking. So privacy of their search has to be a first-class concern.

Pooja Iyer  7:59
That's a good call.

Aisha Tan  8:01
And then the other persona that often gets forgotten is the manager. Managers have two jobs in this system. One, they want to discover talent for openings they are trying to fill. Two, they need to handle the awkwardness when one of their direct reports wants to move. We have to design for both.

Saurabh Mehta  8:21
Yes. The manager being a first-class persona is something I want to make sure we, we hold onto.

Marcus Webb  8:28
On the manager side I want to flag, we have to be careful about creating a marketplace that just becomes a place for managers to poach each other's people without a conversation. That will burn political capital fast.

Pooja Iyer  8:43
Strongly agree. There has to be some protocol around, you know, do you talk to the current manager before or after a formal application. We had this debate at the leadership summit in February. I think the answer is, the employee controls the visibility of their application and the manager finds out at the right time, not too early not too late.

Saurabh Mehta  9:08
Let's put that as an open question. It's a real product policy decision.

Daniel Osei  9:13
Pinning it for later.

Saurabh Mehta  9:15
Marcus from engineering, what's your, what's your initial reaction on technical scope?

Marcus Webb  9:21
Um. Few things. First, identity. We are an Okta shop, SSO is non-negotiable, no separate logins. Second, the integration with Workday — we have to pull positions data, employee profile data, manager hierarchy. The HR data API is rate limited and not great, but we have wrappers. Third, mobile. A lot of our non-desk workforce, especially in our retail and warehouse arms, they don't have a laptop, they have a phone. So mobile-first or at least mobile-friendly. Fourth, search. If search is the experience that matters, we should not, you know, slap an Elasticsearch on it and call it a day. Modern semantic search, with embeddings, makes a real difference for this kind of use case.

Saurabh Mehta  10:08
Agreed on search. I had the same thought.

Marcus Webb  10:11
Fifth thing, notifications. Email, in-app, and probably Teams. Because no one logs in unless something prompts them to.

Pooja Iyer  10:21
That's huge. The current Workday page has no notifications. People forget it exists.

Aisha Tan  10:27
Push notification on Teams when a new role posts matching your skills, I'd open that.

Saurabh Mehta  10:33
Noted. Marcus what about data sensitivity? Profile data, application data, manager visibility — there are real privacy concerns.

Marcus Webb  10:43
Yeah. The principle I want to design around is, the employee owns their data and their visibility. They choose what's on their public profile, who can see they applied, when their current manager finds out. Defaults matter a lot. Defaults should err toward privacy and let the user opt in to more visibility.

Aisha Tan  11:04
Plus one. Defaults to private.

Daniel Osei  11:07
Compliance will also be involved. We have GDPR considerations for our EMEA staff and there are specific German works council rules around what we can do with internal profile data. I will loop in legal early, like, this week.

Saurabh Mehta  11:23
Please do. Last big topic before actions. Success metrics. Pooja what's the headline metric the ELT will want to see?

Pooja Iyer  11:34
Internal fill rate. Today it is somewhere around eighteen percent of open roles get filled internally. The target for the program is thirty percent in twelve months. That's the headline. Secondary metrics are, number of employees who complete a profile, engagement, applications per opening, time to fill internal versus external.

Reema Chakraborty  12:00
And manager NPS on the experience. We had the discussion that managers will sabotage anything they hate.

Marcus Webb  12:08
Realistic.

Saurabh Mehta  12:09
Okay. Five minutes left. Let me try to enumerate actions.

Saurabh Mehta  12:14
Action one, I will write a one-page narrative for the ELT meeting Thursday, covering problem, solution, success metrics, ask. Aisha and Reema I would love your reactions on it by Wednesday end of day.

Aisha Tan  12:28
Works for me.

Reema Chakraborty  12:30
Yes.

Saurabh Mehta  12:31
Action two, Daniel, can you set up the legal and works council intro by end of next week?

Daniel Osei  12:37
Yes, I'll loop in Helena from legal and Karsten from EMEA people partner.

Saurabh Mehta  12:43
Action three, Marcus, can your team scope a rough technical spike on Workday integration capacity? I want to know if the rate limits and data freshness will let us do near-real-time, or if we are looking at, you know, four-hour delayed cache. That affects UX.

Marcus Webb  13:00
Yes, I'll get one of my staff engineers on it. Two weeks.

Saurabh Mehta  13:05
Action four, I will go do six discovery interviews. Two active seekers, two passive explorers, two managers. Aisha can you help me identify candidates?

Aisha Tan  13:16
Yes I'll send a list tomorrow.

Saurabh Mehta  13:18
Action five, parking lot for the policy question on manager visibility timing. We will tackle that in a dedicated session in two weeks once we have interview data.

Pooja Iyer  13:30
Sounds good.

Saurabh Mehta  13:31
Anything I'm missing.

Pooja Iyer  13:34
I would add, can someone audit what's actually working in the current Workday page so we don't throw away anything that is good? Even if it's small.

Reema Chakraborty  13:43
I can ask my team to pull engagement data by feature.

Saurabh Mehta  13:48
Perfect. Action six. Reema to pull current state metrics.

Marcus Webb  13:53
I have to drop. Talk soon.

Saurabh Mehta  13:55
Thanks Marcus. Bye.

Pooja Iyer  13:58
Thank you all. Saurabh I'll send notes after.

Saurabh Mehta  14:02
I have it. Thanks everyone. Recording stopping.

Saurabh Mehta stopped transcription
