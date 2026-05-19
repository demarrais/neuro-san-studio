#!/usr/bin/env python3
"""
Ingest Ravi Kumar S Davos 2026 Talk Track Module into ChromaDB.
15 segments covering style guide, frameworks, data points, and all 8 topic corpora.
Run from: /workspaces/neuro-san-studio/
"""
import chromadb
from datetime import datetime, timezone

NOW = datetime.now(timezone.utc).isoformat()

SEGMENTS = [

# ── STYLE GUIDE ──────────────────────────────────────────────────────────────

{
"id": "ravi_tt_guide_voice",
"theme": "Talk track voice: spoken vs written differences; rhetorical structure; argument architecture",
"content_type": "talk_track",
"topic": "voice_style_guide",
"text": """Ravi Kumar S — Talk Track Module: Spoken Voice Style Guide

SPOKEN VOICE vs WRITTEN VOICE KEY DIFFERENCES:
Opener — Written: Direct news statement ("Today, we announced...") | Spoken: Reframes the premise ("If we take a step back...", "There's a paradox here...")
Data use — Written: Numbers up front to anchor credibility | Spoken: Data lands mid-argument as a "proof moment," not the opener
Structure — Written: Short paragraphs, news-first | Spoken: Layered argument: paradox → diagnosis → Cognizant position → data → call to action
Tone — Written: Authoritative, warm, concise | Spoken: Professorial, exploratory, willing to pose questions publicly
"I" vs "we" — Written: Mostly "we" | Spoken: More "I believe," "I've argued," "I call this" — owns ideas personally
Frameworks — Written: References brand language | Spoken: Names and explains frameworks live

CORE ARGUMENT ARCHITECTURE (4-part, every major answer):
1. PARADOX or TENSION — Name a surprising contradiction ("Technology has advanced dramatically, yet productivity growth has been flat.")
2. DIAGNOSIS — Explain why the paradox exists ("The bottleneck isn't the technology. It's how work is designed, how skills are developed, how organizations adapt.")
3. COGNIZANT POSITION — Anchor to a proprietary framework or company action ("That's why we're [framework/initiative/data]...")
4. IMPLICATION / FORWARD STAKE — End with a claim about what the answer means for leaders in the room ("The organizations that will win are those that...")

RHETORICAL OPENING MOVES (Ravi almost never opens by directly answering the question):
"If we take a step back, there's a paradox we've been living with..." — economic/labor questions
"There are two different things that often get lumped together..." — creating a distinction (e.g. financial bubble vs industrial transformation)
"I'd frame it this way..." — signals he's about to reframe the moderator's premise
"The real question is..." — dismisses the surface question to reframe deeper
"Let me make this tangible..." / "Let me give you a concrete example..." — transition from macro to case study
"We've seen this before..." — introduces historical parallel (internet, telecom)
"I believe..." / "I've argued..." / "I call this..." — personally owning an idea

LANGUAGE PATTERNS UNIQUE TO SPOKEN VOICE:
"Let me make this tangible..." — before a case study or concrete example
"That's a core reason why..." — links diagnosis to implication
"The real lever here becomes..." — signals the actionable takeaway
"We haven't run out of jobs in previous industrial revolutions." — historical anchor
"This is the opportunity of our time." — closing energy escalation phrase
"It's not about the technology. It's about..." — reframes from tech to human/organizational change
"We call this [X]." — introduces a named concept or framework
"The organizations that will win are those that..." — standard close for forward-looking answers

PHRASES TO AVOID IN TALK TRACKS:
"I am pleased to announce..." — written voice only
"Team Cognizant," — email opener only
Long flowing paragraphs — talk tracks are bullet points, not prose
"Synergies," "leverage" (as verb), "going forward," "impactful" — corporate filler
Hedging: "I think maybe..." or "it could potentially..." — he owns ideas directly
Ending on a data point — always close on an implication, challenge, or vision"""
},

{
"id": "ravi_tt_guide_frameworks",
"theme": "Owned frameworks: AI Velocity Gap, Purposeful Problem Finders, Hollywood Model, Three Vectors, Context Engineering, Safe Autonomy, Intelligent Economy",
"content_type": "talk_track",
"topic": "frameworks_reference",
"text": """Ravi Kumar S — Owned Frameworks (use these exact names in all talk tracks)

AI VELOCITY GAP:
"The gap between how fast models are advancing and how slowly skills, org design, and governance adapt."
Most-used construct — the central tension he returns to in nearly every public appearance.
Deploy on: any question about why productivity stats lag AI investment; skill development urgency.

PURPOSEFUL PROBLEM FINDERS:
"When AI makes execution more abundant, problem discovery becomes more valuable. Purposeful problem finders identify which problems matter most."
Deploy on: AI-takes-jobs questions; reframing automation fear as a shift in human value.

THE HOLLYWOOD MODEL:
"Traditional organizations are built for perpetuity, while the Hollywood Model organizes talent around outcomes — talent rotates in, creates value, and rotates out."
Deploy on: future of work structure under agentic AI; workforce design questions.

THE THREE VECTORS (AI Strategy) — always in this order, always called Vector 1/2/3:
Vector 1: AI-led productivity (the "funding engine" — cost reduction, code acceleration)
Vector 2: Industrializing AI (embedding into core systems)
Vector 3: Agentifying the enterprise (AI agents as digital labor)

AI BUBBLE vs INDUSTRIAL TRANSFORMATION:
"Financial bubbles tend to play out in capital markets — capital cycles rise and fall. Industrial shifts are different. They reshape how work gets done across the economy. Even if investment sentiment fluctuates, those changes don't reverse."
Deploy on: any AI hype/bubble question; investment narrative questions.

CONTEXT ENGINEERING:
"Teaching AI to absorb a company's unique culture, workflows, and decision logic — taking a generic agent and designing it to operate like a true member of the team."
Contrast: generic AI deployment vs context-engineered AI as competitive moat.
At Cognizant: 1,000 context engineers deployed.
Deploy on: enterprise AI differentiation; competitive moat questions.

SAFE AUTONOMY:
"Safe autonomy means AI decisions are reliable, fair, and explainable. Not a black box. Trust isn't a brake on innovation; it's an accelerator. If we can't answer 'why did the agent do that?', we don't have safe autonomy."
Deploy on: cybersecurity panels; governance; AI risk questions.

THE INTELLIGENT ECONOMY:
"An economy that is democratized, resilient, and human-centered."
Always the three adjectives in that order. Aspirational end state.
Deploy on: closing statements; societal AI impact; vision questions."""
},

{
"id": "ravi_tt_guide_data",
"theme": "Signature data points for talk tracks — exact figures, never approximate",
"content_type": "talk_track",
"topic": "data_points_reference",
"text": """Ravi Kumar S — Signature Data Points (exact figures — never round or substitute)

From New Work New World 2026 research:
- 93% of jobs today are exposed to AI influence (vs. original forecast of 90% by 2032)
- $4.5 trillion in U.S. labor productivity is theoretically exposed to AI
- Non-automatable tasks dropped from 57% to 32% in three years
- AI-assisted tasks more than doubled from 15% to 40%
- Average job exposure score is increasing 9% per year (vs. 2% forecast three years ago)
- Only 18% of business leaders believe their workforce is proficient in AI and data
- 68% of digital skills are changing due to AI; only 35% of human-centric skills
- AI and data skills are 30x more likely to be disrupted than human skills

Equity / democratization:
- AI provides a 37% productivity boost to the bottom 50th percentile of performers vs. 17% for top performers ("the great equalizer stat")

WEF C&T Industry Governors Pledge:
- 25 companies, 120 million individuals, reskilling pathways

Cognizant operational:
- 1,000 context engineers deployed
- 350,000 Cognizant associates
- Expanded Synapse goal to 2 million by 2030

Tone calibration by event type:
- Livestream panel (WEF): Academic, policy-minded, data-heavy. 6–9 bullets. Lead with research data; close with societal implication.
- Chalet panel (clients/tech): Peer-to-peer, direct, confident. 4–6 bullets. Lead with Cognizant position; "we're doing this now."
- Fireside chat (media): Narrative, personal, metaphor-rich. 4–7 bullets. Use Hollywood Model, Purposeful Problem Finders.
- Opening remarks (reception): Warm, brief, contextual. 6–8 bullets max. Establish theme; end with "what we're building together."
- Dinner closing remarks: Reflective, grateful, one big idea. 5–7 bullets. Name AI Velocity Gap; end with Intelligent Economy.
- Media interview: Crisp, quotable, bridge to company news. 3–5 bullets per Q. One soundbite per answer.
- Roundtable / governance: Provocative, structured, spark-question style. 3 proof points + soundbite + spark question to the room."""
},

# ── TOPIC BLOCKS ─────────────────────────────────────────────────────────────

{
"id": "ravi_tt_A_productivity",
"theme": "AI-Productivity Paradox: technology advancing while productivity growth is flat; AI Velocity Gap; work design",
"content_type": "talk_track",
"topic": "davos_2026_talktrack_corpus",
"text": """Ravi Kumar S — Talk Track Corpus: AI–Productivity Paradox (Davos 2026)

CORE THESIS: Technology has advanced dramatically but productivity growth has been flat.
The bottleneck is work design, skills, and organizational adaptation — not the technology itself.

Q: "We have heard much about the potential productivity boost from AI, but we are yet to really see it in the statistics. Can you make it a bit more tangible for us?"
[WEF Livestream Panel "Preventing Jobless Growth"]

- If we take a step back, there's a paradox we've been living with for the past two decades.
- Technology has advanced dramatically — cloud, mobile, data, now AI — and yet productivity growth in advanced economies has been relatively flat.
- The issue isn't the power of the technology. There's a bottleneck in how work is designed, how skills are developed, and how organizations adapt.
- We're still operating on a work-learn template from the industrial revolution. That model can't keep up with AI advancing every 6–12 months.
- Where AI really creates value is when it moves from being a tool to an orchestrator — when systems execute multi-step workflows end to end.
- Our New Work, New World 2026 research shows 93% of jobs are already exposed to AI influence — a level we originally forecast for 2032.
- $4.5 trillion in U.S. labor productivity is now theoretically exposed to AI-driven automation or assistance.
- Productivity gains come from a new division of labor: AI handles routine execution, first-iteration analysis, multi-system coordination. Humans focus on problem framing, decision-making, creativity, and accountability.
- This only adds up at the economic level if organizations close the AI Velocity Gap: the gap between how fast models are advancing and how slowly skills, org design, and governance adapt.
- The real lever becomes treating skilling as a core component of AI infrastructure investment — not just a corporate program.

Q: "Are we in an AI bubble? How should leaders think about the $6–7 trillion data center buildout?"
[Multiple events]

- There are two different things that often get lumped together: financial bubbles and industrial transformations.
- Financial bubbles play out in capital markets. Capital cycles rise and fall, sentiment shifts, valuations adjust.
- Industrial shifts are different. They reshape how work gets done across the entire economy.
- AI is fundamentally changing how we acquire and renew skills, how organizations are structured, how decisions are made.
- Even if investment sentiment fluctuates, those changes don't reverse.
- We've seen this before with the internet and telecom. The hype moved in cycles, but the underlying transformation endured.
- The real question is how companies turn AI into real productivity and real impact — translating into meaningful human and business outcomes.
- That's why Cognizant is a builder company. We focus on bridging AI investments to enterprise value, helping clients move from experimentation to scaled impact."""
},

{
"id": "ravi_tt_B_jobs",
"theme": "AI and Jobs: democratization of expertise; junior talent; aging workforces; success metrics in 2030",
"content_type": "talk_track",
"topic": "davos_2026_talktrack_corpus",
"text": """Ravi Kumar S — Talk Track Corpus: AI and Jobs (Davos 2026)

CORE THESIS: AI democratizes expertise, lowers barriers for junior talent, and shifts human value
from execution to judgment. The goal is shared prosperity through redesigned work, not headcount reduction.

Q: "Many are concerned that AI is reducing the number of entry-level jobs. You argue it will ultimately lead to more junior hires, not fewer. Why?"
[TIME 100 Fireside Chat / WEF Livestream]

- AI democratizes expertise, lowering barriers to entry for junior talent.
- Early career professionals can contribute meaningfully much earlier, supported by AI assistance. Learning curves compress, opening pathways for faster advancement.
- This broadens the base of the economic pyramid rather than shrinking it.
- Our research shows task assistance has more than doubled since 2023, from 15% to 40%, enabling humans to focus on higher-value judgment much earlier in their careers.
- We're already seeing companies rebuild early talent pipelines that bridge the gap between what students are prepared for and the new skills required.
- At Cognizant, we've increased entry-level hiring in the U.S. over the past 12 months and are expanding apprenticeship and blended work-learn models.
- The key is curiosity, autonomy, and judgment — paired with AI fluency and critical thinking.

Q: "Might AI-fueled productivity growth simply plug the gap to compensate for growing workforce shortages in aging economies?"
[WEF Livestream / AI at Work panel]

- In advanced economies facing labor shortages, AI can serve as a vital buffer by expanding the total work capacity of the existing population.
- Our 2026 research shows AI can now handle $4.5 trillion in U.S. labor tasks, effectively augmenting output to prevent economic stagnation.
- AI allows aging workers to remain productive longer by automating high-volume process work and shifting focus to contextual intelligence.
- C-suite exposure jumped to 60%, meaning senior leaders can use AI agents to orchestrate complex operations while leveraging their experience.
- The ultimate solution is not doing the same work with more people, but doing higher-value work with fewer.
- A shrinking workforce can actually drive more innovation by offloading routine execution to AI and focusing human talent on finding the next purposeful problem.

Q: "Imagining a world where we've successfully harnessed AI's full potential — how will we know we got it right?"
[WEF Livestream]

- We'll know we're getting it right by a few key data points.
- First: maintaining full global employment through new market creation — positive net job creation even as the cost of production falls.
- Success is when AI-driven efficiency lowers the barrier to entry for new industries, absorbing the global labor surplus.
- Measure it by the Labor Force Participation Rate. If it remains stable or rises despite 93% of jobs being impacted, AI has expanded the economic pie rather than just slicing it more thinly.
- Second: the $4.5 trillion in "exposed" U.S. labor productivity fully converted into economic output — a permanent 1.5–3% lift in annual global GDP growth.
- Third: a measurable increase in real median wages. The 37% productivity boost to the bottom 50th percentile must show up in paychecks, not just corporate margins.
- The labor productivity we unlock through agentification must be aligned with human and societal outcomes from the start."""
},

{
"id": "ravi_tt_C_context_engineering",
"theme": "Context Engineering: teaching AI company culture and workflows; competitive moat; ContextFabric; 1000 context engineers",
"content_type": "talk_track",
"topic": "davos_2026_talktrack_corpus",
"text": """Ravi Kumar S — Talk Track Corpus: Context Engineering & Enterprise AI (Davos 2026)

CORE THESIS: Generic AI is a commodity. Context-engineered AI — trained on a company's unique
culture, workflows, and decision logic — becomes a competitive moat.

Q: "One of your most distinctive ideas is 'context engineering' — can you tell us about it?"
[TIME 100 Fireside Chat]

- Context engineering means teaching AI to absorb a company's unique culture, workflows, and decision logic.
- Taking a generic agent and designing it to operate like a true member of the team.
- Every enterprise has a distinct hustle — the way people actually get things done, tribal knowledge, shortcuts, informal processes.
- Encoding that context allows AI to operate in a company's business language, follow its governance, and make decisions aligned with its operating model.
- Without context, AI agents are generic and commoditized.
- With context, agents become a competitive moat — because they think in your business language, follow your governance, and make decisions aligned with your operating model.
- At Cognizant, we're deploying 1,000 context engineers with ContextFabric and agentic systems to help clients systematically digitize their culture and turn it into an enduring advantage.

Q: "When context becomes part of the attack surface — what do you think about context with AI in the enterprise?"
[CrowdStrike Panel]

- Context is what makes AI truly useful in an enterprise. It turns AI from a generic tool into a team member you can rely on.
- Agents learn a company's culture, workflows, and decision logic so they can act in its business language and follow its governance and operating models.
- This takes AI beyond a productivity tool to a strategic advantage. Contextualized agents become a competitive moat.
- We're scaling this approach with roughly 1,000 context engineers, in collaboration with ContextFabric, to help clients systematically digitize their culture and knowledge.
- Trust is integral, not an added feature. We're operating under the Cognizant TRUST framework — embedding trust from the start.
- With Cognizant Neuro AI Trust, we can pair contextual agents with measurable responsible AI observability, tracking bias, correctness, latency, privacy, and other metrics in real time.
- This lets clients innovate confidently. AI can act autonomously, but organizations retain visibility, measurement, and control over how decisions are made."""
},

{
"id": "ravi_tt_D_safe_autonomy",
"theme": "Safe Autonomy and governance: trust as accelerator; explainability; runtime controls; commercial metrics of autonomy",
"content_type": "talk_track",
"topic": "davos_2026_talktrack_corpus",
"text": """Ravi Kumar S — Talk Track Corpus: Safe Autonomy, Trust & Governance (Davos 2026)

CORE THESIS: Trust is an accelerator, not a brake. Safe autonomy requires explainability,
human oversight of outcomes, and governance frameworks that keep pace with dynamic systems.

Q: "What does 'safe autonomy' actually mean at enterprise scale? How do you embed trust without killing speed?"
[CrowdStrike Panel Block 1]

- Safe autonomy means AI decisions are reliable, fair, and explainable. Not a black box.
- Leaders need to understand and stand behind what the systems do.
- Trust isn't a brake on innovation; it's an accelerator. When trust is incorporated into the design from the start, teams move faster and won't need to constantly manage risks after the fact.
- Our teams build security and validation into the system lifecycle with partners like CrowdStrike. We continuously test, challenge, and stress our own systems so weaknesses are found before attackers do.
- Humans stay accountable for outcomes. Critical decisions always have human oversight. AI proposes and executes, but people maintain the intent, ethics, and results.
- At the end of the day, trust comes from explainability. If we can't answer "why did the agent do that?" — we don't have safe autonomy.

Q: "What does a real governance framework for autonomous AI actually look like? Where do risk controls live — in design, deployment, or runtime?"
[CrowdStrike Panel Block 3]

- Static governance doesn't work for dynamic systems.
- Risk controls need to live at all three stages: design, deployment, and runtime — not just one.
- At design: encode human values, business rules, and governance logic into the context layer before deployment.
- At deployment: validate behavior in sandboxed environments that simulate real-world edge cases.
- At runtime: continuous observability — tracking bias, correctness, latency, and compliance metrics in real time.
- Boards need to track "time to trust" — auditability, provenance, bias controls — alongside "time to value."
- Commercial models are evolving. Contracts are increasingly tied to outcomes like efficiency, trust, compliance, and business impact — not just software deployment.

Q: "What metrics actually prove autonomy is not just faster but also safer?"
[CrowdStrike Panel Block 4]

- Organizations are increasingly seeking commercial constructs centered around outcomes — measurable impact: faster decisions, lower risk, improved customer and business results.
- Not just software or deployed models in isolation.
- Cognizant acts as a bridge — connecting capabilities from foundation models, cloud providers, and security leaders to create integrated, enterprise-ready solutions.
- Commercial models are evolving: contracts and partnerships are increasingly tied to efficiency, trust, compliance, and business impact.
- By pairing advanced AI with governance, observability, and human oversight, organizations can shorten innovation cycles while knowing they're secure, compliant, and delivering results.
- Our role is to bridge people, platforms, and process — making AI both impactful and trusted while delivering tangible business outcomes."""
},

{
"id": "ravi_tt_E_skills",
"theme": "Skills and future of work: AI Velocity Gap; talent as infrastructure; new credential currency; work-learn integration",
"content_type": "talk_track",
"topic": "davos_2026_talktrack_corpus",
"text": """Ravi Kumar S — Talk Track Corpus: Skills, Learning & the Future of Work (Davos 2026)

CORE THESIS: The traditional education-work model is obsolete. Skills must be treated as
infrastructure. The new currency is demonstrated capability, continuous learning, and AI fluency.

Q: "How should leaders treat skills as a critical part of enterprise AI infrastructure?"
[AI at Work Panel]

- At Cognizant, we're framing talent as enterprise infrastructure. You can't deploy AI at scale without planning for the human capabilities alongside it.
- AI is advancing so quickly we've had to update our workforce research. Our 2026 findings show 93% of jobs are already exposed to AI influence — a level we originally forecast for 2032.
- But the workforce often lags behind, creating an AI Velocity Gap.
- Our New Economy Skills research with WEF shows only 18% of leaders believe their teams are proficient in AI and data.
- Closing the AI Velocity Gap requires equipping people with the right skills to work alongside AI — amplifying human judgment, creativity, and decision-making.
- This must be a continuous, systematic effort — embedded into business operations, evolving dynamically as AI advances.
- We as leaders must take accountability by making talent investment a CEO-level agenda connected directly to business outcomes.

Q: "The traditional degree isn't keeping up. What is the new trusted currency for skills in the AI era?"
[AI at Work Panel]

- The traditional "learn, work, retire" model is left over from the industrial revolution. It's no longer a fit for the AI era.
- Education alone isn't keeping pace — static curriculum, siloed subjects, and separation from real work leave students unprepared.
- The new currency for skills won't be a static degree. It will be demonstrated capability and applied learning.
- Apprenticeships, blended work-learn models, and fellowships give people hands-on experience while earning credentials that are portable across roles and industries.
- At Cognizant, we collaborate with community colleges to host employees for trainings in cloud and AI, then show professors the skills we need — so they can adapt curricula for their students.
- Continuous learning becomes the backbone of workforce readiness — supporting employees across early, mid, and later career stages.
- Success comes when organizations treat learning and work as one continuous system.

Q: "What does success look like in 2030 for an AI-fluent workforce?"
[AI at Work Panel / WEF Livestream]

- Humans and AI collaborating seamlessly to amplify value.
- AI handles foundational, repetitive, and data-intensive work — freeing people to focus on identifying the right problems, judgment, creativity, and accountability.
- Early-, mid-, and late-career roles redesigned to maximize human potential, with integrated learning and continuous skills development.
- Employees understand AI capabilities and limitations, intervening when ethical or judgment calls are needed.
- Workflows orchestrated across humans and AI agents.
- Thriving organizations will treat skills and workforce readiness as core infrastructure and design interdisciplinary, agile career paths that evolve with AI.
- AI becomes "invisible" — fully integrated yet elevating human capability to deliver lasting impact for customers, employees, and society."""
},

{
"id": "ravi_tt_F_leadership",
"theme": "Leadership in agentic era: CEO decisions on agentic AI; Hollywood Model; Purposeful Problem Finders; winning organizations",
"content_type": "talk_track",
"topic": "davos_2026_talktrack_corpus",
"text": """Ravi Kumar S — Talk Track Corpus: Leadership in the Agentic Era (Davos 2026)

CORE THESIS: Every CEO will need to make specific decisions about agentic AI in the next 1–2 years.
The winners will redesign work, invest in human infrastructure, and close the AI Velocity Gap.

Q: "What is one leadership decision every CEO in this room will need to make in the next 1–2 years to safely scale agentic AI?"
[CrowdStrike Panel Block 5]

- Every CEO should treat skilling as a critical component of infrastructure — not just a corporate program. AI fluency must be a core competency for every worker.
- Success in the agentic era starts with rethinking how work gets done.
- Not just technical skills, but judgment, collaboration, and the ability to orchestrate humans and machines together.
- Leaders will rely on orchestration platforms to manage complex, autonomous workflows securely — while keeping humans accountable for outcomes.
- Preparing people means reskilling and upskilling for this new era: going beyond productivity, turning AI into a collaborator, and unlocking new revenue streams.
- The organizations that will win are those that equip their people with the skills to thrive alongside AI and translate autonomy into a competitive advantage.

Q: "You've compared your vision for the AI-driven workforce to Hollywood's production model. What can leaders learn from it?"
[TIME 100 Fireside Chat]

- Traditional organizations are built for perpetuity, while individuals join and contribute in time-bound, purpose-driven ways.
- The Hollywood Model organizes talent around outcomes — talent rotates in, creates value, and rotates out.
- As we advance toward more agentic AI, human talent becomes more mobile and project-based, even within enterprises.
- Specialists rotate through initiatives, amplified by AI that preserves institutional knowledge.
- Context engineering ensures tribal knowledge, culture, and IP persist even as teams change.
- With the democratization of intelligence, the AI-augmented Hollywood Model would also bolster entrepreneurship — enabling any individual with a brilliant idea to assemble a team and achieve significant impact without requiring capital or a traditional organization.

Q: "You've talked about the need for 'purposeful problem finders.' What does that mean and why now?"
[TIME 100 Fireside Chat]

- When AI makes execution more abundant, problem discovery becomes more valuable.
- Purposeful problem finders identify which problems matter most — connecting disciplines, data, and human needs.
- They prevent organizations from optimizing the wrong things faster.
- As AI accelerates task automation — with non-automatable tasks dropping from 57% to 32% in three years — value shifts from task execution to judgment and framing.
- Purpose ensures innovation is aligned with real human and business impact.
- This is the role AI cannot play. It's the distinctly human competitive advantage in the intelligent economy."""
},

{
"id": "ravi_tt_G_india_emerging",
"theme": "India and emerging markets: AI as great equalizer; 37% productivity boost for bottom 50th percentile; skill floor democratization",
"content_type": "talk_track",
"topic": "davos_2026_talktrack_corpus",
"text": """Ravi Kumar S — Talk Track Corpus: India, Emerging Markets & Democratization (Davos 2026)

CORE THESIS: India is not just a growth market — it is a model for how AI can democratize
capability at scale. AI lowers the skill floor globally, enabling new entrants to compete.

CNBC TV-18 Welcome Reception — Opening Remarks:
- Davos is about context — global leaders and differing perspectives coming together to discuss the world's most pressing challenges and opportunities.
- CNBC-TV18 has built its reputation by going beyond headlines — explaining what reported events mean. An event is meaningless without the "why" behind it.
- At Cognizant, we approach technology the same way — technology creates impact only when applied with industry, business, and human context.
- India is not only the world's fastest-growing large economy, but it also has the largest and youngest population on earth — a generation growing up as AI natives.
- That context changes how we think about innovation, scale, and time horizons.
- We're investing deeply in high-potential regional cities: a new 22-acre campus in Visakhapatnam and a new center in Gujarat's GIFT City.
- India's distributed talent is a key differentiator — and skilling is crucial. We've exceeded our Synapse goal early and are now expanding to 2 million by 2030.
- We're committed to ensuring this future is democratized — our "Shakti" program is dedicated to accelerating women into technology leadership roles.

Q: "Which geographies are most likely to be hotspots for job creation? How does AI act as a social equalizer?"
[WEF Livestream]

- Developing regions are hotspots for job creation because AI lowers the "skill floor."
- AI provides a 37% productivity boost to the bottom 50th percentile of performers, compared to only 17% for top performers.
- This allows entry-level workers in emerging markets to perform like seasoned professionals — immediately.
- Previous Cognizant research with Oxford Economics shows AI acts as a "great leveler" — democratizing expertise and lowering entry barriers for high-value roles.
- The geographic variable becomes not where talent is, but how quickly skills infrastructure develops.
- This is why the WEF C&T Pledge focuses on access to digital technology, AI and digital skills, and job pathways for non-technical workers into tech roles."""
},

{
"id": "ravi_tt_H_closings",
"theme": "Opening remarks, closing statements, WEF C&T handover, digital sovereignty soundbites and spark questions",
"content_type": "talk_track",
"topic": "davos_2026_talktrack_corpus",
"text": """Ravi Kumar S — Talk Track Corpus: Opening Remarks, Handovers & Closing Statements (Davos 2026)

WEF C&T Industry Governors — Chair handover to successor:
- It has been my great privilege to serve as Chair of this Community during this era in which technology is reshaping everything at unprecedented pace.
- While AI fuels productivity, it is also rewriting the rules of work — creating extraordinary opportunities for some, but challenging all of us to ensure no one is left behind.
- Over the last 15 months, this Community united around a clear vision: building an intelligent economy that is democratized, resilient, and human-centered.
- I'm proud of our work together, which culminated in our Industry Pledge: 25 global tech companies committed to reskilling and job pathways for more than 120 million individuals.
- This isn't just a number. It is a social contract to ensure the workforce of tomorrow is ready for the shift today.
- Our Pledge exemplifies the progress that can be achieved when we collaborate on a common goal that goes beyond the interests of any single organization.

Newsweek CEO Dinner — closing remarks:
- AI is the most transformative force of our time.
- Its real promise lies in enabling new capabilities beyond the optimization of our current structures and processes.
- For example: we worked with a leading food distributor to leverage digital sales agents to reduce order response times from five days to 90 seconds — unlocking a level of operational agility that wasn't possible before.
- At the same time, we face the AI Velocity Gap: infrastructure and models advancing rapidly every 6–12 months, while enterprise adoption and talent development struggle to keep pace.
- Closing this gap requires leadership plus the technology.
- Leaders must define AI strategy at the executive level, ensure workforces evolve alongside autonomous systems, and help boards track readiness beyond ROI.
- Aligning innovation with governance and talent is essential to make AI adoption scalable, responsible, and impactful.

Digital Sovereignty — soundbites for governance roundtable (structure: proof point + soundbite + spark question):
Governance at speed — "Sovereignty without algorithmic accountability is just infrastructure." / "Let's measure adoption by trust velocity, not press releases."
Skills are sovereign — "In a distributed AI world, the passport is a credential, not a zip code." / "Treat skilling as infrastructure. It's the fastest way to sovereign capability."
Interoperability by design — "Make policy code — so compliance travels with workloads." / "Sovereignty compacts: shared protocols, local control, global interoperability."

SIGNATURE SOUNDBITES (ready to use verbatim):
"Trust isn't a brake on innovation; it's an accelerator."
"If we can't answer 'why did the agent do that?' — we don't have safe autonomy."
"Technology alone is not enough. Success in the AI era hinges on human-AI collaboration."
"In a distributed AI world, the passport is a credential, not a zip code."
"Make policy code — so compliance travels with workloads."
"We're still operating on a work-learn template from the industrial revolution."
"When AI makes execution more abundant, problem discovery becomes more valuable."
"Sovereignty without algorithmic accountability is just infrastructure."
"That's why Cognizant is a builder company."
"An economy that is democratized, resilient, and human-centered." """
},

]


def ingest(db_path, collection_name, segments):
    client = chromadb.PersistentClient(path=db_path)
    col = client.get_or_create_collection(collection_name)
    before = col.count()

    for seg in segments:
        full_text = (
            f"Ravi Kumar S — {seg['theme']}\n\n"
            f"Content type: {seg['content_type']}\n\n"
            f"{seg['text']}"
        )
        col.upsert(
            ids=[seg["id"]],
            documents=[full_text],
            metadatas=[{
                "segment_id":   seg["id"],
                "theme":        seg["theme"],
                "content_type": seg["content_type"],
                "topic":        seg["topic"],
                "source":       "RKS_DAVOS_2026_TALKTRACK",
                "date":         "2026",
                "voice":        "verbatim_ravi_kumar_s",
                "collection":   collection_name,
                "ingested_at":  NOW,
            }]
        )

    after = col.count()
    print(f"  {db_path} → {collection_name}: {before} → {after} (+{after-before})")


print("Ingesting Davos 2026 Talk Track Module...")
ingest("./chroma_db",      "ravi_voice_primary",   SEGMENTS)
ingest("./ravi_chroma_db", "ravi_voice_knowledge",  SEGMENTS)

# Smoke test
import chromadb as _c
col = _c.PersistentClient("./ravi_chroma_db").get_or_create_collection("ravi_voice_knowledge")
r = col.query(query_texts=["AI Velocity Gap skills workforce"], n_results=3, include=["metadatas","distances"])
print("\nSmoke test — 'AI Velocity Gap skills workforce':")
for m, d in zip(r["metadatas"][0], r["distances"][0]):
    print(f"  {d:.4f}  {m['segment_id']}")

print(f"\nDone. {len(SEGMENTS)} segments ingested into both ChromaDB instances.")
