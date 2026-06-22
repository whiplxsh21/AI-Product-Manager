# Compass — Customer Support Knowledge Hub: Leadership Discovery

**Date:** February 26, 2026
**Time:** 4:00 PM – 4:51 PM
**Duration:** 51m 18s
**Meeting Type:** Microsoft Teams Recording
**Attendees:**
- Rohan Sharma — VP, Customer Experience
- Eleni Demetriou — Director, Global Support Operations
- Kevin Brennan — Senior Manager, Knowledge Management
- Asha Pillai — Director, Engineering (CX Platform)
- Cara Whitfield — Senior Product Manager (driver)

Recording started by Cara Whitfield

---

Cara Whitfield  0:03
Recording on. Audio levels good for everyone? Asha I noticed you had some echo last time.

Asha Pillai  0:11
I'm on the wired headset now, should be fine.

Cara Whitfield  0:14
Great. So today's agenda. Forty-five minutes plus buffer. We are kicking off the discovery for what's been called the support knowledge platform, working name Compass. The questions I want to answer are, one, what is broken about how we manage support knowledge today, two, what does success look like, three, who are the users, and four, what are the technical constraints. Rohan I know you have hard stop at four-fifty.

Rohan Sharma  0:45
Yes four-fifty I have a board prep call.

Cara Whitfield  0:48
Got it. Let's go. Rohan can you set the strategic context first.

Rohan Sharma  0:53
Sure. The number one thing the board has been asking is, why are our CSAT scores trending down. Our CSAT was eighty-seven percent in twenty-four and we are at eighty-one now. That's not catastrophic but it's a real trend. When we dug in, two findings. First, average time to resolution has gone from eleven minutes to nineteen. Second, the percentage of tickets requiring escalation has gone from twenty-two to thirty-one percent. Agents are taking longer and escalating more, which means they don't have the answers they need.

Eleni Demetriou  1:34
And the agent population has not gotten less experienced. Tenure is actually up. The job has gotten harder because our product surface has grown — we acquired two companies last year, we launched four new modules. The knowledge base hasn't kept up.

Kevin Brennan  1:54
That's putting it generously. The knowledge base is a mess. We have, depending on how you count, somewhere between four and six knowledge bases. Salesforce KB has the legacy stuff, Confluence has the modern stuff, there's an internal wiki the support engineering team uses, the product teams maintain their own runbooks, and the acquired companies came with their own KBs that we never migrated. Six places to look.

Rohan Sharma  2:26
Six places. So when an agent gets a question they don't know, where do they go?

Eleni Demetriou  2:32
Slack. They ask their team in Slack. The answer comes from whoever happens to be online, which is luck of the draw.

Kevin Brennan  2:42
Or they ask one of two or three tribal experts, who get pinged constantly. We have a real shadow knowledge problem.

Cara Whitfield  2:51
So the real source of knowledge is in people's heads and Slack channels, not in formal KBs.

Eleni Demetriou  2:58
Correct. The KB articles we have are written, but agents don't search them because they can't find what they need with the search.

Cara Whitfield  3:08
Why can't they find what they need.

Kevin Brennan  3:12
Two reasons. One, search is keyword and it's brittle. If the article says "session expiry" and the customer is asking about "I got logged out", the search misses. Two, even when the article exists, the agent has to construct the right query, scan results, click into articles, read paragraphs to find the relevant piece. Average article is two thousand words. The actual answer is one paragraph.

Asha Pillai  3:43
That's an interesting framing. The unit of value isn't the article, it's the paragraph or step.

Kevin Brennan  3:50
Right. Modern KB design needs to surface the answer, not the article.

Cara Whitfield  3:55
That's a key principle. Agents want answers, not articles.

Rohan Sharma  4:01
Let's also talk about the second half of the problem. The agent finds nothing, so they escalate. The escalation queue is, frankly, a nightmare. It's a different system, it requires re-typing the customer context, and the escalation specialists are themselves overloaded. Average escalation resolution time is two and a half days.

Eleni Demetriou  4:25
And customers wait. CSAT correlates strongly with time to resolution. If we can prevent half the escalations by giving agents better answers, we move CSAT meaningfully.

Cara Whitfield  4:40
Got it. So the problem statement is, agents can't find consistent, current, fast answers in our existing knowledge base, leading to long resolution times and high escalation rates, which hurts CSAT. And the secondary problem is, our knowledge isn't being captured in the first place because there's no easy way for tribal experts to contribute.

Rohan Sharma  5:04
Yes. I would add a third dimension. Even when we have good articles, they go stale. We have articles from twenty twenty-two that reference UI elements that haven't existed for a year.

Kevin Brennan  5:18
We have, roughly, fourteen hundred articles. Last review date varies. About a quarter haven't been touched in eighteen months.

Cara Whitfield  5:28
Staleness, captured. Three-part problem. Discovery, capture, freshness.

Cara Whitfield  5:34
Let's talk users. Eleni you run support ops, who are the users we are building for.

Eleni Demetriou  5:41
Primary user is the front-line agent. Eleven hundred of them globally. They live in their ticketing tool which is Zendesk. The KB needs to come to them in Zendesk, not be a separate app they have to open.

Cara Whitfield  5:57
Embedded in Zendesk. Critical constraint.

Eleni Demetriou  6:01
Yes. Second user is the escalation specialist. About a hundred of them. They have more complex needs and they need to see the full context.

Eleni Demetriou  6:12
Third user is the knowledge author, which is Kevin's team primarily but also subject matter experts in product and engineering who get drafted in.

Kevin Brennan  6:23
About fifty people across the company are formal or informal contributors. Right now they have to fight with our Confluence templates and the publishing workflow is six steps.

Cara Whitfield  6:35
Fourth user, you mentioned tribal experts. Are they distinct from authors?

Kevin Brennan  6:41
They are. Authors are people who want to write. Tribal experts are people who get asked. They wouldn't sit down to write an article but if you put a tool in front of them that's lightweight enough, they'd contribute.

Cara Whitfield  6:54
So a low-friction contribution path for experts is its own user need.

Kevin Brennan  7:00
Yes. The dream is, expert answers a Slack question, the tool says "want to save that as a knowledge entry?", they click yes, it's published with light review.

Cara Whitfield  7:13
That's a wedge feature. Note it.

Rohan Sharma  7:16
Fifth user, me. I want analytics. I want to see which articles are doing the work, which queries return nothing, where the gaps are.

Cara Whitfield  7:27
Analytics for management. Persona five, ops leadership.

Cara Whitfield  7:32
Okay solution direction. Let me share my thinking and you push back. Compass is, at its core, a semantic search and answer layer over our knowledge content, embedded in Zendesk, with a lightweight authoring experience for contributors and an analytics layer for management. The search is natural language. The result is an answer not a list of articles. The answer cites its sources. Agents can give feedback on answers in one click. Authoring is fast and the publishing workflow is short.

Asha Pillai  8:11
Let me unpack the technical assumptions. Semantic search means embeddings. Embeddings means a vector database. We have a pilot of pgvector that works for small corpora. Fourteen hundred articles is small. We can fit on pgvector for v1.

Cara Whitfield  8:31
Good.

Asha Pillai  8:33
Answer generation is an LLM. We have an enterprise OpenAI contract with data isolation. That's the path of least resistance for v1. Long-term we want flexibility but for v1 OpenAI is fine and is what legal has signed off on.

Cara Whitfield  8:51
Captured.

Asha Pillai  8:53
Embedding in Zendesk, we can use their app marketplace SDK. We've built Zendesk apps before. The constraint is the side panel real estate, it's narrow, around three hundred forty pixels. Designs need to respect that.

Cara Whitfield  9:10
Narrow side panel as the primary surface. Captured.

Asha Pillai  9:15
On the question of where articles live. Option A, keep them in Confluence and pull them into our index. Option B, migrate everything into a Compass-native CMS. Option B is cleaner long-term but a migration is expensive. Option A is faster.

Kevin Brennan  9:35
The Confluence content is the cleanest portion of our knowledge. The Salesforce KB and the other places are a mess. Long-term we want one home. Short-term, I'd say, build the search to work over all sources but have a Compass-native authoring experience for new content, and migrate the legacy stuff opportunistically over time.

Asha Pillai  9:59
That works. Index multiple sources for search. New content authored in Compass.

Cara Whitfield  10:06
Captured. Compass authoring is the new path. Existing content remains where it lives but is indexed.

Eleni Demetriou  10:14
We should also talk about article confidence. The agent needs to trust the answer or they won't use it. If the answer is wrong sometimes the trust collapses.

Cara Whitfield  10:26
That's the LLM hallucination problem. How do we mitigate.

Asha Pillai  10:31
Strict retrieval-augmented generation. The LLM only generates answers from retrieved articles. Every answer cites the exact article and ideally the exact paragraph. If retrieval doesn't find good sources, the answer is "I don't have a confident answer, here are some related articles" rather than a made-up answer.

Cara Whitfield  10:54
Citation per paragraph. Captured. No-confidence fallback. Captured.

Kevin Brennan  10:59
Agents also need a one-click way to say "this answer is wrong" or "this answer is missing context". That feedback should route to my team for review.

Cara Whitfield  11:11
Feedback loop with routing. Captured.

Eleni Demetriou  11:14
On the analytics side, two metrics matter most for me at the team level. First, how often does Compass produce an answer the agent uses, measured by the agent clicking "this answered my question" or by the ticket being resolved without escalation. Second, where are the gaps — what queries returned no good answer.

Cara Whitfield  11:38
Answer utilization and gap analysis. Captured.

Rohan Sharma  11:43
Higher level metric for me, ticket resolution time. We want to see that drop. And escalation rate drop.

Cara Whitfield  11:51
Resolution time, escalation rate. Captured.

Cara Whitfield  11:55
Out of scope for v1. Customer-facing knowledge portal, right? Self-service for end customers.

Eleni Demetriou  12:03
Right, agent-facing only. The customer portal is a separate roadmap item.

Cara Whitfield  12:09
Out of scope. Multi-language. We have multi-language requirements eventually but for v1 English only.

Kevin Brennan  12:18
English only for v1, agreed.

Cara Whitfield  12:21
Mobile, I assume agents are on desktops.

Eleni Demetriou  12:25
Yes desktops. Mobile is not needed.

Cara Whitfield  12:28
Out of scope. Integration with other ticketing platforms beyond Zendesk?

Eleni Demetriou  12:34
Out of scope for v1.

Cara Whitfield  12:36
Last topic before actions. Timeline.

Rohan Sharma  12:41
Board has heard about this. They want to see something live before end of fiscal year. That's October. So we have eight months from now.

Cara Whitfield  12:53
Eight months for a v1 with the scope we just discussed. Aggressive but feasible if we keep discipline. I'll come back next session with a phased plan — search and embedded Zendesk experience first, authoring second, analytics third.

Rohan Sharma  13:11
Sounds good. I have to drop.

Cara Whitfield  13:13
Thanks Rohan. Bye.

Rohan Sharma  13:15
Bye.

Cara Whitfield  13:17
Okay actions for the rest of us. I'll draft a product brief by next Monday. Kevin can you do an audit of all current knowledge sources and a quality assessment of each, by end of next week?

Kevin Brennan  13:31
Yes.

Cara Whitfield  13:32
Asha can you scope the RAG architecture in more depth and identify which of our existing infrastructure we use, by end of next week?

Asha Pillai  13:42
Yes I'll write a technical design doc.

Cara Whitfield  13:46
Eleni can you arrange for me to shadow three agents next week? I want to see the workflow in their actual environment.

Eleni Demetriou  13:54
Yes I'll set that up.

Cara Whitfield  13:56
Alright thanks everyone. Stopping the recording.

Cara Whitfield stopped transcription
