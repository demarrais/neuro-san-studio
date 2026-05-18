#!/usr/bin/env python3
"""
Ingest JPMorgan 2026 Global Technology, Media & Communications Conference
transcript into Ravi Kumar S's voice corpus (both ChromaDB instances).

Run from: /workspaces/neuro-san-studio/
Usage:    python3 ingest_jpmorgan_2026.py [--dry-run]

Targets:
  ./chroma_db          collection: ravi_voice_primary
  ./ravi_chroma_db     collection: ravi_voice_knowledge
"""

import sys
import os
import hashlib
import textwrap
import argparse
from datetime import datetime

# ── Dependency check ────────────────────────────────────────────────────────
try:
    import chromadb
except ImportError:
    sys.exit("chromadb not found. Run: pip install chromadb --break-system-packages")

# ── Transcript source ────────────────────────────────────────────────────────
# Full verbatim Ravi Kumar S remarks extracted from the transcript.
# JPMorgan questions are included only as minimal context anchors,
# clearly labeled so the editorial gate can identify speaker attribution.

TRANSCRIPT_METADATA = {
    "source_event":  "JPMorgan 2026 Global Technology, Media and Communications Conference",
    "source":        "RKS_JPM_TMC_2026",
    "date":          "2026",
    "voice":         "verbatim_ravi_kumar_s",
    "topic":         "jpmorgan_tmc_2026_conference",
    "speaker":       "Ravi Kumar S",
    "interviewer":   "JPMorgan analyst",
    "content_type":  "verbatim_transcript",
    # Applies to all gate content types — this is raw voice material,
    # not a published artifact, so no gate-type restriction.
    "usable_for":    "blog,linkedin,white_paper,social,press_release,letter,transcript",
}

# Each entry is a thematically coherent segment of Ravi's remarks.
# Keeping segments thematic (not purely character-count) preserves
# meaning and improves retrieval precision.
TRANSCRIPT_SEGMENTS = [
    {
        "id":    "ravi_jpm_tmc26_001",
        "theme": "Security as Y2K moment; vulnerability discovery and remediation at machine speed",
        "text":  (
            "Security led, with the mythos of 5.5 GPT, where you could do vulnerability discovery "
            "at machine speed, but you can equally remediate, refactor, and patch at machine speed. "
            "And that opportunity is almost like a Y2K moment for us, because as you open the lid, "
            "you don't just look at one thing; you look at brittle code, you look at design deficiencies, "
            "you do a whole lot of refactoring. So the ability to take your old stuff, pull in new ways "
            "to do it, underwrite that capital for the new things."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_002",
        "theme": "New terrain: applying software to operations; deterministic vs non-deterministic work",
        "text":  (
            "Now, what I'm talking about is a completely new terrain, which is primarily applying "
            "software to operations of companies. Historically, portions of those operations which were "
            "deterministic in nature were done by classical software. Portions of the things which were "
            "not deterministic, which had judgment, which could not be codified, we put into human effort."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_003",
        "theme": "Healthcare platform example; $500B spend; $4T administrative opportunity; self-funded transition",
        "text":  (
            "Just as an example, the healthcare platforms in Cognizant have a flow-through of $500 billion "
            "of spend flowing through our platforms. I do healthcare operations for our clients. Now I could "
            "identify another $4 trillion of work, which is administrative in nature. Remember, healthcare has "
            "20 million people working. Only five to six million people do care. Fourteen to fifteen million "
            "people do administrative work. I could identify it. Now, that doesn't need big discretionary spend. "
            "You just have to front-load it. You have to transition human labor to digital labor. It is "
            "self-funded. So you could take those steps even in an uncertain situation. This is what I do "
            "with clients. Yesterday I was in my healthcare conference, we had 1,000 clients there. And "
            "the ability to take some of that and put it back into care, I think is a phenomenal example."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_004",
        "theme": "AI capability gap to production value; contextual technology; bridge thesis",
        "text":  (
            "In summary, the framing I have in my mind is the AI capability is absolutely moving at a rapid "
            "pace. The bridge to production value has a big gap. The more the capability is, the more the "
            "production value gap is. And what does production value mean? This is a contextual technology. "
            "Production value means you have to ground the technology into what clients want their work to "
            "be transferred to AI, which means workflows, controls, guardrails, trust layers, evals, context, "
            "and the tribal knowledge, all of that put together. The more the technology is evolving, the more "
            "the technology is advancing, the more is the gap to enterprise value. Not for software engineering. "
            "Software engineering is already mainstream. I'm talking about operations of companies."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_005",
        "theme": "Infrastructure build-out; $1T spent; $2-3T ahead; agentifying operations as bridge",
        "text":  (
            "If a trillion dollars was spent in the last one year on infrastructure build-out, another two "
            "to three trillion dollars is going to be spent in the next two to three years. All of that "
            "build-out will only stack up if you are able to apply it to operations of companies. And the "
            "bridge to enterprise value, the bridge to enterprise production value, I think is a big gap. "
            "So clients are asking me, how do we actually bridge that gap? So that conversation is happening "
            "now, so therefore I'm actually much more optimistic about how AI is a tailwind to our industry. "
            "You need a ton of work to be done to get to that production value. And the production value will "
            "come from agentifying finance operations, legal operations, HR operations, customer service, and "
            "vertical operations like healthcare, mortgage operations, a whole bunch of things which were a "
            "human endeavor."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_006",
        "theme": "Active pipeline: mainframe, SAP, Mythos 5.5 GPT discoveries; layering value pools",
        "text":  (
            "Two or three weeks is too little to really change the paradigm. But the one thing I can "
            "certainly tell you is everything I said so far is no longer conversations yet to happen. "
            "The conversation is happening now. I already have a large mainframe deal where I'm transitioning "
            "work to AWS Cloud. I have at least five to six SAP migrations happening. I have 10 to 12 "
            "discoveries happening on Mythos and 5.5 GPT. So those conversations are accelerated."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_007",
        "theme": "Layering growth: consolidation, new value pools of old things in new ways, inflection point thesis",
        "text":  (
            "I would say if you go back to the last two years, the industry was layering consolidation and "
            "expansive spend related to consolidation as a growth lever. That is right at the base. I'm "
            "layering in these new value pools of old things done in new ways, which is unlocking mainframes, "
            "unlocking SAP migrations, unlocking vulnerabilities on landscapes, and layering it further. Once "
            "I layer in the spend on the operations, which is also self-funded, it doesn't need so much "
            "discretionary because you are actually eliminating work versus creating more work. Once the unlock "
            "on growth happens, you are going to use the same set of people to create more throughput. So "
            "you're going to see new products and new services powered by AI. So if you put that layering in, "
            "you're going to see an inflection point at some point of time."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_008",
        "theme": "Capability-to-production-value gap framing; BPO double digit; infrastructure growth; breakaway growth ambition",
        "text":  (
            "My framing is completely changed. My framing now is the capability is right up there and it is "
            "further going up. The production value is here and the gap is huge. That gap needs a bridge, and "
            "that bridge will come from companies like us. Financial services for Cognizant is already "
            "double-digit growth. My BPO operations, which is where the expansive opportunity is, have been "
            "double digit for two years in a row. Infrastructure services, because there's a sprawl of "
            "infrastructure, are close to double-digit growth. Software engineering is deflationary. The "
            "expansion attached to software engineering is taking off now. So we just have to keep layering "
            "this, and we'll be back to industry-leading growth. We are already in the winner's circle, and "
            "I'm less interested anymore about being on the top of the heap. I just want to take this to "
            "breakaway growth."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_009",
        "theme": "OpenAI/Anthropic deploy co response; enterprise heterogeneity; bridge endorsement thesis",
        "text":  (
            "It doesn't change anything. Actually, on the contrary, it reinforces the fact that there is a "
            "gap between production value and the capability of these models. We underestimate the "
            "heterogeneity of enterprises. We underestimate the fact that this is a contextual science. "
            "Everything which was supposed to be deterministic has already been in classical software. "
            "This is deterministic; it has to be grounded, it has to be harnessed. So on the contrary, "
            "it reinforces the fact that we need that bridge. You can argue whether that bridge will be "
            "companies like us, or whether it will be new companies coming into the picture. I don't think "
            "those deployment companies have been built for scale. I don't think it is built to monetize "
            "the bridge. It has been built to get access to the distribution network, which is needed, and "
            "that distribution access always was the reason when new technology came into picture."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_010",
        "theme": "Historical precedent: Oracle consulting, SaaS professional services, cloud — deployment cos never scaled to global 2000",
        "text":  (
            "When enterprise software came into picture, we had Oracle consulting in the mix. When SaaS "
            "software came into picture, we had professional services supporting SaaS software. When cloud "
            "adoption happened, we had professional services coming into picture. But it never took off at "
            "scale to build what is needed for the global 2000. So I see this as an endorsement of what we "
            "do. I see this as an endorsement that this bridge is needed."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_011",
        "theme": "Reforged first principles: system integrator to AI builder; pyramid to interdisciplinary; project to operational outcomes",
        "text":  (
            "Do we need to do it differently? Yes. Everybody's now talking about a forward deployment engineer. "
            "Forward deployment engineer was the perfect thing in the last few years, when the world view was "
            "that everything was broken in an enterprise, you had to bring everything together, you go with "
            "the machine and you tie it together. The world view is no longer about everything is broken. "
            "The world view is that you want to take this machine, which has digital labor, along with you, "
            "and you want it to be integrated, and you want to deliver an outcome. So we have to reforge our "
            "first principles. Our first principles have to be reforged where we go from a system integrator "
            "to an AI builder. We go from a pyramid of talent to integrated interdisciplinary talent with "
            "human and digital labor. We go from a services company to a platform services company. We go "
            "from managing project outcomes to managing operational outcomes for enterprises."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_012",
        "theme": "Frontier engineers and frontier operators defined; KYC example; healthcare operations example",
        "text":  (
            "The roles we need now are frontier engineers and frontier operators. Frontier engineers being "
            "people who can engineer, equivalent to, in a way, a forward engineer. The machine that time was "
            "an ontology with machine learning. Now the machine is generative AI. You also need frontier "
            "operators. What I mean by frontier operators is if clients are going to run operations with us, "
            "some clients are actually going to say, you run those operations for me with human and digital "
            "labor. I have five banks who are doing know your customer with me. They don't want to outsource "
            "that function. What they're essentially saying is, we love what you're saying on agentic. We "
            "want to agentify it. Give me a fixed-price proposal for agentifying know your customer. There's "
            "another set of clients who come and told me, here is the stuff which you do in healthcare today "
            "on your platform. There is a ton of labor sitting outside. It couldn't be codified. Please "
            "agentify and run those operations for me."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_013",
        "theme": "New-age BPO with digital labor; BPO already double-digit; frontier operators own operational outcomes",
        "text":  (
            "So I need a BPO professional who can work with digital labor and have an integrated digital "
            "and human labor and actually deliver an outcome. That is the new-age BPO we are actually "
            "building, and my BPO business is already double-digit growth. So you need frontier engineers "
            "for things which you want to engineer for your clients, agentic. You need frontier operators "
            "for things which you want to actually own the outcomes, operational outcomes."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_014",
        "theme": "Trizetto: perpetual to subscription to BPaaS; per member per month; claimless world; platforms thesis",
        "text":  (
            "With Trizetto, we are going from perpetual license to subscription license to BPass. Now we "
            "are working on per member per month to manage lives. It doesn't matter what transactions. In "
            "fact, in an ideal world, you shouldn't have transactions. You shouldn't have claims. It should "
            "be a claimless world. So just manage per person per month. Here is the menu card. So we have "
            "to be a platforms company. Either we have to build our platforms, or we have to work with "
            "third-party SaaS companies and integrate their platforms into our services. Because clients are "
            "neither going to look for SaaS software on its own in some places, nor are they going to look "
            "for services. They're going to look for AI outcomes."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_015",
        "theme": "Tokenization thesis: A0-A3 rate card; clients asking Cognizant to take on token risk; institutional harness",
        "text":  (
            "Tokenization has become a huge thesis for me. In my earnings, I spoke about AI-enabled rate "
            "cards. A0 being human effort, A1 being human effort validated by machines, A2 being machine "
            "effort validated by humans, and A3 being autonomous. Now clients are saying, as you go from "
            "A0 to A3, the premium on the rates will go up, but the number of units will go down, because "
            "there's machines attached to it. Clients have started to say, wait a minute, you want to take "
            "the human effort accountability, I'm going to take the machine effort and I don't know how to "
            "do this. So take this over and run. Which then means I should build a harness around "
            "tokenization. Why? Because I could do it with hundreds of clients, so I should be able to do "
            "the same things in a compounding way."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_016",
        "theme": "Tokenization as new functional value; metering leaves institutional harness; community knowledge compounding",
        "text":  (
            "That's how clients did. Now tokenization could be a new functional value for IT services. So "
            "we have metered inside the company projects, people, and the kind of work we do. That metering "
            "leaves an institutional harness. Earlier, it was in the minds of people and repeatable artifacts. "
            "Now it is in the harness. I should be able to deliver your digital labor more reliably, cheaper, "
            "and more predictably, which means I take a higher risk on tokenization, higher risk on inference "
            "costs or tokens, if I'm doing operations. If I'm doing development work, the token costs are "
            "less risky. So we have now started to build a craft on tokenization, and this is a discussion "
            "many of my clients are doing now. They're saying my bills are going up. Would you be able to "
            "take this over? We use the tokens to process invoices or process claims. For each of them, we "
            "have a way to spec it, a way to size it, and a way to price it."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_017",
        "theme": "Tokenization: scale advantage over clients; consumption vs value measurement; craft-building",
        "text":  (
            "So that's a new mode, and it will come from the community knowledge of clients, because if "
            "you do it at 30 places or 50 places or 100 places, you'll be able to do it better than your "
            "clients. So that's the craft we are building. Is it completely efficient? Not yet. Am I going "
            "to falter? Maybe yes. But I'm going to build a moat, which will help the tokenization process "
            "to be more scientific, versus today trying to measure tokenization based on consumption versus "
            "measuring on value."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_018",
        "theme": "Tokenization risk management; inference vs development risk; swim lanes; compounding via community learning",
        "text":  (
            "In software engineering, the risk is low. You're also developing something; you're not running "
            "it. The cost of tokenization is a higher risk in inference and lower risk in developing. If "
            "you're running operations of companies, you have to be precise on the tasks you want to do for "
            "a client, and you should be able to spec the job. So you have to pick your swim lanes where "
            "you want to. You could be blind-sided by things with high inference costs. I'm not going to "
            "run wild on this model. I'm going to run in a controlled way to figure out which swim lanes "
            "we can precisely size and which swim lanes we'll have throughput so that we can build patterns "
            "and therefore the compounding effect. The compounding effect is similar to autonomous cars. "
            "Autonomous cars drive better than you not because they have your learning. They do better "
            "than you because they have community learning."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_019",
        "theme": "Tokenization moat durability; utility cost scenario; velocity and reliability as drivers",
        "text":  (
            "Is this going to be a long-lasting moat? I don't know. If the cost of tokens is so low that "
            "it's like a utility, then cost is not going to be a driver. It has to be driven by velocity "
            "and, because it's a contextual science, it's also driven by reliability and predictability."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_020",
        "theme": "Adoption timeline: historically outsourced verticals easier; legal/HR harder; healthcare as priority; Trizetto moat",
        "text":  (
            "The ones which have been historically outsourced, like healthcare operations, mortgage "
            "operations, customer service, and F&A functions, are easy or relatively easy. The ones which "
            "have been historically not done, like legal operations, have not been outsourced to companies "
            "like us. HR operations have not been; that will be harder. The vertical ones are a longer "
            "runway; the horizontal ones have a lesser opportunity, because the vertical ones actually have "
            "the most administrative labor, which can be shrunk. I told you about healthcare just as an "
            "example. Twenty million people work in healthcare, five to six million people really do care, "
            "14 to 15 million people do other things. It's a high-churn industry, so it's not like "
            "employability is on a sustainable basis. So I think we have to pick the right ones. Healthcare "
            "is certainly one I'm picking. I want to make sure that the hustle is around Trizetto, so the "
            "rules engine of Trizetto is where we want the real moat to be, from which agents are accessing "
            "rules and guardrails and everything else."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_021",
        "theme": "Billing systems, life insurance, mortgage as classical software underperformers becoming AI opportunities",
        "text":  (
            "If I have to pick a few more at a high level, wherever classical software did it in a less "
            "effective way, like billing systems or record-keeping systems in life insurance or mortgage "
            "operations, those are the places. They are not the best-looking things in classical software. "
            "They potentially become the best-looking things for AI."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_022",
        "theme": "Progress metrics: revenue per person, margin per person; pyramid broadening via LEAP; platform play",
        "text":  (
            "I think what you have to judge companies in this sector, including us, is whether we are... "
            "Revenue per person, margin per person is an important metric. I'd say revenue per person and "
            "margin per person, because I've changed my pyramid mix. With our LEAP program, what I'm really "
            "saying is the pyramid is broader and the pyramid is shorter. I'm delayering the nodes where "
            "there is administrative work and I'm only having player-coaches in the middle, and I'm hiring "
            "significantly more people at the bottom, higher than last year, and last year we hired higher "
            "than the year before. That will give me margin per person higher, but it will not give me "
            "revenue per person higher because I'm broadening the pyramid. I want to create the right "
            "balance. Revenue per person and margin per person on a TTM basis have just about gone to "
            "double digits, so we have to expand that. The platform play will allow us to increase the "
            "revenue per person and the margin per person because platforms are an important part of my "
            "thesis."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_023",
        "theme": "Platforms group; venture arm; build/buy/invest/partner; Anthropic, OpenAI, Gemini as frontier machines; certification metric",
        "text":  (
            "We have set up a new platforms group, dedicated. Some we're going to build, some we're going "
            "to buy, some we're going to invest in. We put up a venture arm a few weeks ago, and some "
            "we're going to partner with third parties. I think the throughput from the three frontier "
            "model companies, Anthropic, OpenAI, and Gemini, all three are going to be super important, "
            "because that's the machine we are carrying now. I'm measuring it on certifications, which is "
            "an external metric. That is something I'm very keen to pursue. And I think for our scale, "
            "that's the kind of capacity needed to bridge capability to production value, at scale, at much "
            "better economics. So if you put all of this together, we should start to go back to growth "
            "rates which make the industry attractive."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_024",
        "theme": "M&A thesis: platforms and operations only; Australia (Astreya) rationale: infrastructure sprawl, per-user, autonomous workplace",
        "text":  (
            "We did a buyback this morning, for a billion dollars. We increased it by a billion dollars. "
            "We had a billion dollars of buyback in January, and we felt like that was a great way to show "
            "confidence and back our story. I think the M&A we do should fall into this thesis of platforms "
            "or operations, and we'll be very purposeful in doing that. Australia has not closed yet, but "
            "one of the reasons why Australia made phenomenal sense to us is the infrastructure sprawl which "
            "is going to happen. We are already close to double-digit growth in infrastructure. We felt it "
            "is an extraordinary opportunity for workplace services, data services, data center services, "
            "and network services. That's what the company does. And it doesn't do it on human effort. It "
            "does it on a user basis. So they do it on per-user basis, and they do autonomous infrastructure "
            "in workplaces. So it's a complementary capability, platform-led, and a new outcome-based model, "
            "because it is not based on human effort; it is based on number of users."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_025",
        "theme": "Strategic M&A intent: APAC and Europe gaps; M&A strategy anchored in platforms and operations only",
        "text":  (
            "Would we be opportunistic in places where we have lower presence? For example, I have less "
            "presence in Asia Pacific, I have less presence in Europe. Of course, we'll do it, but my "
            "general strategic intent on M&A is to layer platforms and operations, because that's where "
            "the bridge to enterprise value, the bridge to enterprise production value, is very high."
        ),
    },
    {
        "id":    "ravi_jpm_tmc26_026",
        "theme": "Forward-looking metrics to track: fixed price growth, outcome-based pricing, AI rate cards, platforms group progress",
        "text":  (
            "Certainly revenue per person, margin per person is one metric to watch. I would say more "
            "fixed price, more outcome-based pricing. We have 50% fixed price, 10% outcome based. So that "
            "will be... we moved, we flipped the whole thing. We almost added 10% into fixed price in the "
            "last three years from 2023 to now. Fixed price, because the engineering on AI, where people "
            "are not willing to give you the operations, will potentially go fixed price. AI-infused rate "
            "cards are also new stuff. It might show up on time and material, but it is new stuff because "
            "I'm infusing digital labor and I've put this new stack, and we are the only one who are "
            "actually propagating this to our clients. But that will be another metric to say we are "
            "progressing that way. The work we do with our platforms group is a very important change in "
            "our reforged first principles. The work we can do on outcomes is a combination of fixed price "
            "and time and materials, and fixed price and transaction-based or outcome-based pricing. These "
            "are the reforged first principles on which you should see whether we're progressing in the "
            "right direction with the right velocity."
        ),
    },
]

# ── ChromaDB targets ─────────────────────────────────────────────────────────
DB_CONFIGS = [
    {
        "path":       "./chroma_db",
        "collection": "ravi_voice_primary",
        "label":      "PRIMARY",
    },
    {
        "path":       "./ravi_chroma_db",
        "collection": "ravi_voice_knowledge",
        "label":      "KNOWLEDGE",
    },
]


# ── Helpers ──────────────────────────────────────────────────────────────────
def build_document_string(seg: dict) -> str:
    """Format segment for storage: includes event header and theme tag."""
    return (
        f"Ravi Kumar S — JPMorgan 2026 Global Technology, Media and Communications Conference\n"
        f"Theme: {seg['theme']}\n\n"
        f"{seg['text']}"
    )


def build_metadata(seg: dict) -> dict:
    """Merge global transcript metadata with per-segment fields."""
    meta = dict(TRANSCRIPT_METADATA)
    meta["segment_id"]    = seg["id"]
    meta["theme"]         = seg["theme"]
    meta["char_count"]    = len(seg["text"])
    meta["ingested_at"]   = datetime.utcnow().isoformat()
    meta["title"]         = f"JPM TMC 2026 — {seg['theme'][:60]}"
    return meta


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def ingest_to_collection(client, cfg: dict, segments: list, dry_run: bool) -> dict:
    """Upsert all segments into a single ChromaDB collection. Returns stats."""
    col = client.get_or_create_collection(
        name=cfg["collection"],
        metadata={"hnsw:space": "cosine"},
    )
    existing_ids = set(col.get(include=[])["ids"])

    added, skipped, updated = 0, 0, 0

    for seg in segments:
        doc_text = build_document_string(seg)
        meta     = build_metadata(seg)
        doc_id   = seg["id"]
        chk      = content_hash(seg["text"])
        meta["content_hash"] = chk

        if doc_id in existing_ids:
            # Check if content has changed
            existing = col.get(ids=[doc_id], include=["metadatas"])
            old_hash = existing["metadatas"][0].get("content_hash", "")
            if old_hash == chk:
                skipped += 1
                print(f"  [SKIP]    {doc_id}  (unchanged)")
                continue
            else:
                action = "UPDATE"
                updated += 1
        else:
            action = "ADD"
            added += 1

        print(f"  [{action}]   {doc_id}  — {seg['theme'][:55]}")

        if not dry_run:
            col.upsert(
                ids=[doc_id],
                documents=[doc_text],
                metadatas=[meta],
            )

    return {"added": added, "skipped": skipped, "updated": updated,
            "total_in_collection": col.count() if not dry_run else "n/a (dry-run)"}


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Ingest JPM 2026 TMC transcript into Ravi voice corpus")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing to ChromaDB")
    args = parser.parse_args()

    if args.dry_run:
        print("\n⚡ DRY RUN — no data will be written\n")

    print(f"Segments to process: {len(TRANSCRIPT_SEGMENTS)}")
    print(f"Source: {TRANSCRIPT_METADATA['source_event']}\n")

    results = {}

    for cfg in DB_CONFIGS:
        db_path = cfg["path"]
        label   = cfg["label"]

        if not os.path.isdir(db_path):
            print(f"\n⚠  [{label}] ChromaDB path not found: {db_path}")
            print("   Skipping — run from /workspaces/neuro-san-studio/")
            results[label] = "PATH_NOT_FOUND"
            continue

        print(f"\n{'─'*60}")
        print(f"[{label}] {db_path}  →  collection: {cfg['collection']}")
        print('─'*60)

        try:
            client = chromadb.PersistentClient(path=db_path)
            stats  = ingest_to_collection(client, cfg, TRANSCRIPT_SEGMENTS, dry_run=args.dry_run)
            results[label] = stats
            print(f"\n  ✓ Added: {stats['added']}  |  Updated: {stats['updated']}  |  Skipped: {stats['skipped']}")
            print(f"  ✓ Total docs in collection: {stats['total_in_collection']}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results[label] = f"ERROR: {e}"

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("INGESTION SUMMARY")
    print('='*60)
    for label, stats in results.items():
        if isinstance(stats, dict):
            print(f"  {label:12s}  added={stats['added']}  updated={stats['updated']}  "
                  f"skipped={stats['skipped']}  total={stats['total_in_collection']}")
        else:
            print(f"  {label:12s}  {stats}")

    if args.dry_run:
        print("\n⚡ DRY RUN complete — re-run without --dry-run to commit.")
    else:
        print("\n✓ Ingestion complete. Restart the Ravi twin server to load updated corpus:")
        print("  lsof -ti :8080 | xargs kill -9 && ./start_ravi.sh")


if __name__ == "__main__":
    main()
