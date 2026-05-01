"""
editorial_gate_tool.py

EditorialGateTool for the Ravi Kumar S digital twin.
Enforces voice fidelity, editorial quality, and semantic similarity
against the verbatim transcript stored in ChromaDB (ravi_voice_primary).

Supports content_type parameter for per-format opener/closer standards:
  transcript   — verbatim spoken word (default, strictest)
  blog         — written long-form thought leadership
  white_paper  — formal research/policy document
  social       — LinkedIn or short-form post
  press_release — quote or statement for media
  letter       — direct address to an individual or group

Neuro SAN coded tool — invoke via agent network or CLI test harness.
"""

import json
import os
import re
import sys
from typing import Any

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


# ── Gate Configuration ────────────────────────────────────────────────────────

CHROMA_DB_PATH       = "./chroma_db"
COLLECTION_NAME      = "ravi_voice_primary"
SIMILARITY_THRESHOLD = 0.75
TOP_K_CHUNKS         = 3

# Banned words — violate Ravi's voice standards
BANNED_WORDS = [
    "utilize", "synergy", "synergize", "holistic", "ecosystem",
    "bandwidth", "circle back", "deep dive", "boil the ocean",
    "move the needle", "low-hanging fruit", "paradigm shift", "value-add",
    "learnings", "ideate", "socialize", "democratize", "empower",
    "transformative", "game-changer", "revolutionary",
    "cutting-edge", "best-in-class", "world-class", "robust",
    "actionable insights", "thought leader", "pivot",
    "hollywood-style", "intentionality and purpose", "co-creation",
    "currency of success", "the road ahead", "meaningful impact for all",
    "at the forefront", "ensures", "hopefully", "we trust",
    "leaning into", "reshaping the playing field",
]

# ── Per-Content-Type Opener/Closer Standards ──────────────────────────────────

OPENER_STANDARDS = {
    "transcript": {
        "signals": [
            "i mean", "you know", "um,", "uh,", "the reality is",
            "i would say", "look,", "here's the thing", "let me",
            "if you reflect", "i actually", "i think",
        ],
        "description": (
            "Opener should have spoken cadence: 'I mean,', 'You know,', "
            "'The reality is...', 'I would say...'"
        ),
    },
    "blog": {
        "signals": [
            "talk of", "what happens when", "the question is not",
            "every ", "the ", "there is a ", "there are ", "we are ",
            "two years ago", "for years", "the most ", "industry ",
            "something is ", "a new ", "this is not ", "when ",
            "93%", "90%", "50%", "nearly", "the single",
        ],
        "description": (
            "Blog opener should be a direct provocation, statistic, or strong claim. "
            "Examples: 'Talk of an AI bubble is overblown.' / "
            "'What happens when society embraces a technology faster than it can absorb its consequences?'"
        ),
    },
    "white_paper": {
        "signals": [
            "the evidence", "this paper", "across industries", "the data",
            "for the past", "over the last", "research indicates",
            "the question before", "three forces", "four forces",
            "the central argument", "this analysis", "the case for",
            "industry value", "the fundamental", "as of ",
        ],
        "description": (
            "White paper opener should establish the research frame, central argument, "
            "or the key evidential claim being examined."
        ),
    },
    "social": {
        "signals": [
            "i", "we", "the ", "what ", "why ", "how ", "here's",
            "a question", "three things", "one thing", "something ",
            "unpopular opinion", "hot take", "fact:", "truth:",
        ],
        "description": (
            "Social post opener should be direct and attention-grabbing. "
            "First person or a punchy declarative claim."
        ),
    },
    "press_release": {
        "signals": [
            "today", "announced", "cognizant", "the acquisition",
            "the partnership", "this collaboration", "this agreement",
            "we are", "i am", "this marks", "the combination",
        ],
        "description": (
            "Press release opener should state the news, company, or action directly. "
            "Ravi quotes should anchor on strategic significance, not pleasantries."
        ),
    },
    "letter": {
        "signals": [
            "i am writing", "i want to", "as we", "over the past",
            "this has been", "when i reflect", "i have spent",
            "the work we", "to our", "dear ", "colleagues,",
            "i believe", "one year ago", "two years ago",
        ],
        "description": (
            "Letter opener should establish personal voice and direct address. "
            "First person, reflective or purposeful tone."
        ),
    },
}

CLOSER_STANDARDS = {
    "transcript": {
        "signals": [
            "so", "and that is", "that is the", "which means", "therefore",
            "because", "if we can", "only if", "the ones who", "that's the power",
            "that is the power",
        ],
        "description": (
            "Closer should end declaratively: 'That is the power of...', "
            "'And only if we...', 'Which means...'"
        ),
    },
    "blog": {
        "signals": [
            "will come from", "will not come from", "the ones who",
            "that is the", "only if", "the most important",
            "will define", "will redefine", "what this moment",
            "the question is", "the answer is", "that is what",
            "outcomes.", "the future.", "value.", "results.",
            "understands this.", "chooses this.", "demands this.",
        ],
        "description": (
            "Blog closer should end with a forward-looking provocation or declarative claim. "
            "Model: 'The most important innovation of the coming decade will not come from "
            "artificial intelligence. It will come from empowering every worker to use it.'"
        ),
    },
    "white_paper": {
        "signals": [
            "this requires", "the implication is", "the recommendation",
            "organizations that", "companies that", "the firms that",
            "the path forward", "the evidence points", "what this means",
            "the industry must", "leaders must", "requires action",
            "the window", "this is the moment", "the decision",
        ],
        "description": (
            "White paper closer should end with a policy recommendation, "
            "call to action, or evidence-grounded forward claim."
        ),
    },
    "social": {
        "signals": [
            "agree?", "thoughts?", "what do you think?", "worth reading.",
            "share this.", "the future is", "this is why", "it matters.",
            "that's the shift.", "the question is", "are you ready",
            "will you", "join us", "link in bio", "link below",
        ],
        "description": (
            "Social closer should invite engagement or land a punchy final claim."
        ),
    },
    "press_release": {
        "signals": [
            "together", "at scale", "for our clients", "for enterprises",
            "the future of", "this is what", "this is how",
            "value for", "outcomes for", "results for",
            "forward.", "ahead.", "next.", "possible.",
        ],
        "description": (
            "Press release quote closer should land on strategic significance "
            "or client/market impact. Not a pleasantry."
        ),
    },
    "letter": {
        "signals": [
            "thank you", "i am grateful", "with confidence", "with optimism",
            "forward together", "ahead of us", "what we build",
            "the work continues", "i look forward", "sincerely",
            "the opportunity ahead", "what comes next",
        ],
        "description": (
            "Letter closer should end with gratitude, forward orientation, "
            "or a call to shared action."
        ),
    },
}

# Attribution framing
ATTRIBUTION_PHRASES = [
    "as i call it", "as we call it", "i've written", "i've spoken",
    "what i mean by", "in my", "we call it", "i would say",
    "i mean,", "you know,", "i have spoken",
]

# Framework vocabulary
FRAMEWORK_VOCABULARY = [
    "first principles", "1st principles", "reforge", "digital labor",
    "ai builder", "context engineering", "probabilistic", "deterministic",
    "vector 1", "vector 2", "vector 3",
    "a1", "a2", "a3", "a4", "rate card",
    "outcome", "underwriting", "player coach", "agent manager",
    "verification economy", "pyramid", "interdisciplinary",
    "system integrator", "frontier model", "neural network",
    "throughput", "platform shift", "swim lane", "value engine",
    "labor-based", "outcome-based", "managed services",
]


# ── Individual Gate Checks ────────────────────────────────────────────────────

def check_banned_words(text: str) -> dict:
    text_lower = text.lower()
    found = [w for w in BANNED_WORDS if w in text_lower]
    return {
        "passed": len(found) == 0,
        "check": "banned_words",
        "violations": found,
        "message": (
            f"Banned words detected: {found}. Remove these — they violate Ravi's voice."
            if found else "No banned words detected."
        ),
    }


def check_opener_quality(text: str, content_type: str = "blog") -> dict:
    standard = OPENER_STANDARDS.get(content_type, OPENER_STANDARDS["blog"])
    first_150 = text[:150].lower()
    found = [s for s in standard["signals"] if s in first_150]
    passed = len(found) > 0
    return {
        "passed": passed,
        "check": "opener_quality",
        "content_type": content_type,
        "signals_found": found,
        "message": (
            f"Opener meets {content_type} standard."
            if passed else
            f"WEAK OPENER: \"{text[:80].lower()}\". {standard['description']}"
        ),
    }


def check_closer_quality(text: str, content_type: str = "blog") -> dict:
    standard = CLOSER_STANDARDS.get(content_type, CLOSER_STANDARDS["blog"])
    last_150 = text[-150:].lower()
    found = [s for s in standard["signals"] if s in last_150]
    passed = len(found) > 0
    return {
        "passed": passed,
        "check": "closer_quality",
        "content_type": content_type,
        "signals_found": found,
        "message": (
            f"Closer meets {content_type} standard."
            if passed else
            f"WEAK CLOSER: {standard['description']}"
        ),
    }


def check_framework_vocabulary(text: str) -> dict:
    text_lower = text.lower()
    found = [v for v in FRAMEWORK_VOCABULARY if v in text_lower]
    passed = len(found) >= 2
    return {
        "passed": passed,
        "check": "framework_vocabulary",
        "terms_found": found,
        "message": (
            f"Framework vocabulary present: {found}"
            if passed else
            f"Too few framework terms. Found only: {found}. "
            f"Output should use at least 2 of Ravi's established vocabulary."
        ),
    }


def check_attribution_framing(text: str) -> dict:
    text_lower = text.lower()
    found = [p for p in ATTRIBUTION_PHRASES if p in text_lower]
    passed = len(found) >= 1
    return {
        "passed": passed,
        "check": "attribution_framing",
        "phrases_found": found,
        "message": (
            "Attribution framing present."
            if passed else
            "No attribution framing. Ravi uses phrases like 'as I call it', "
            "'as we call it', 'what I mean by', 'I've spoken about this'."
        ),
    }


def check_header_structure(text: str) -> dict:
    lines = text.split("\n")
    header_lines = [l.strip() for l in lines if l.strip().startswith("#")]
    passed = len(header_lines) == 0
    return {
        "passed": passed,
        "check": "header_structure",
        "header_lines_found": header_lines,
        "message": (
            "No markdown headers — correct format."
            if passed else
            f"Output contains markdown headers which break voice fidelity. "
            f"Use verbal numbering, not headers. Found: {header_lines}"
        ),
    }


def check_list_format(text: str) -> dict:
    violations = []
    lines = text.strip().split("\n")
    for line in lines:
        stripped = line.strip()
        if re.match(r'^\d+[\.\):]', stripped):
            violations.append(f"Numbered list item: {stripped[:60]}")
        if re.match(r'^(Vector|Step|Phase|Stage|Point)\s+\d+[:\-]', stripped, re.IGNORECASE):
            violations.append(f"Labeled list item: {stripped[:60]}")
    passed = len(violations) == 0
    return {
        "passed": passed,
        "check": "list_format",
        "violations": violations,
        "message": (
            "No prohibited list formatting."
            if passed else
            f"Numbered or labeled list items found. Use prose instead: {violations}"
        ),
    }


def check_em_dashes(text: str) -> dict:
    count = len(re.findall(r"—|(?<!-)--(?!-)", text))
    word_count = len(text.split())
    allowed = max(1, word_count // 500)
    passed = count <= allowed
    return {
        "passed": passed,
        "check": "em_dash_count",
        "em_dashes_found": count,
        "word_count": word_count,
        "allowed": allowed,
        "message": (
            f"Em-dash usage OK: {count} in {word_count} words."
            if passed else
            f"EM-DASH OVERUSE: {count} found in {word_count} words. Max {allowed}. "
            "Replace excess with commas, colons, or periods."
        ),
    }


def check_semantic_similarity(text: str) -> dict:
    if not CHROMA_AVAILABLE:
        return {
            "passed": True,
            "check": "semantic_similarity",
            "skipped": True,
            "message": "chromadb not installed — semantic check skipped.",
        }
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        collection = client.get_collection(name=COLLECTION_NAME)
        results = collection.query(
            query_texts=[text],
            n_results=TOP_K_CHUNKS,
            include=["metadatas", "distances", "documents"],
        )
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]
        documents = results["documents"][0]
        avg_distance = sum(distances) / len(distances)
        min_distance = min(distances)
        passed = avg_distance <= SIMILARITY_THRESHOLD
        top_matches = [
            {
                "chunk_id": m.get("chunk_id", "unknown"),
                "topic":    m.get("topic", "unknown"),
                "distance": round(d, 4),
                "excerpt":  doc[:120] + "...",
            }
            for m, d, doc in zip(metadatas, distances, documents)
        ]
        return {
            "passed": passed,
            "check": "semantic_similarity",
            "avg_distance": round(avg_distance, 4),
            "min_distance": round(min_distance, 4),
            "threshold": SIMILARITY_THRESHOLD,
            "top_matches": top_matches,
            "message": (
                f"Semantic similarity OK — avg cosine distance {avg_distance:.4f}."
                if passed else
                f"Semantic drift — avg cosine distance {avg_distance:.4f} "
                f"exceeds threshold {SIMILARITY_THRESHOLD}."
            ),
        }
    except Exception as e:
        return {
            "passed": False,
            "check": "semantic_similarity",
            "error": str(e),
            "message": f"ChromaDB query failed: {e}.",
        }


def check_statistics(text: str) -> dict:
    found = re.findall(
        r"\d+\.?\d*\s*%|\d+\.?\d*x\b|\d{4}\s*occupations|\d+,\d+\s*tasks"
        r"|\d+\s*professions|\$[\d\.]+[BMT]|\d+\s*basis points",
        text.lower()
    )
    passed = len(found) >= 2
    return {
        "passed": passed,
        "check": "statistics",
        "stats_found": found,
        "message": (
            f"Statistics present: {found}"
            if passed else
            "MISSING STATISTICS: Must include at least 2 corpus-verified figures. "
            "Call memory_query_tool to retrieve verified statistics before writing."
        ),
    }


# ── Main Gate Orchestrator ────────────────────────────────────────────────────

class EditorialGateTool:
    """
    Neuro SAN coded tool.
    Pass any candidate output through all editorial gates.
    Returns structured pass/fail report with per-check detail.

    content_type options: transcript, blog, white_paper, social, press_release, letter
    Defaults to 'blog' if not specified.
    """

    def get_tool_name(self) -> str:
        return "editorial_gate_tool"

    def get_instructions(self) -> str:
        return (
            "Evaluate any candidate output for voice fidelity and editorial quality. "
            "Pass the full candidate text as 'candidate_text'. "
            "Optionally pass 'content_type' to apply per-format standards: "
            "transcript, blog, white_paper, social, press_release, letter. "
            "Defaults to 'blog'. "
            "Returns a structured gate report. If gate_passed is False, "
            "revise output to address failed_checks before finalizing."
        )

    def get_args_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "candidate_text": {
                    "type": "string",
                    "description": "Full candidate output text to evaluate.",
                },
                "content_type": {
                    "type": "string",
                    "description": (
                        "Content format for per-type opener/closer standards. "
                        "Options: transcript, blog, white_paper, social, "
                        "press_release, letter. Defaults to blog."
                    ),
                },
            },
            "required": ["candidate_text"],
        }

    def invoke(self, args: dict[str, Any]) -> dict[str, Any]:
        candidate_text = (
            args.get("candidate_text")
            or args.get("draft")
            or args.get("text")
            or ""
        )
        content_type   = args.get("content_type", "blog").lower().strip()

        if content_type not in OPENER_STANDARDS:
            content_type = "blog"

        if not candidate_text.strip():
            return {
                "gate_passed": False,
                "error": "candidate_text is empty.",
                "checks": [],
            }

        checks = [
            check_banned_words(candidate_text),
            check_opener_quality(candidate_text, content_type),
            check_closer_quality(candidate_text, content_type),
            check_framework_vocabulary(candidate_text),
            check_attribution_framing(candidate_text),
            check_header_structure(candidate_text),
            check_list_format(candidate_text),
            check_semantic_similarity(candidate_text),
            check_statistics(candidate_text),
            check_em_dashes(candidate_text),
        ]

        failed = [c for c in checks if not c["passed"]]
        passed_checks = [c for c in checks if c["passed"]]
        gate_passed = len(failed) == 0

        return {
            "gate_passed": gate_passed,
            "status": "PASS" if gate_passed else "GATE_FAILURE",
            "violations": [c["message"] for c in failed],
            "content_type": content_type,
            "total_checks": len(checks),
            "passed_count": len(passed_checks),
            "failed_count": len(failed),
            "failed_checks": [c["check"] for c in failed],
            "summary": (
                "All editorial gates passed. Output is voice-faithful."
                if gate_passed else
                f"{len(failed)} gate(s) failed: {[c['check'] for c in failed]}. "
                "Revise output before finalizing."
            ),
            "checks": checks,
        }


# ── CLI Test Harness ──────────────────────────────────────────────────────────

if __name__ == "__main__":

    BLOG_SAMPLE = (
        "Talk of an AI bubble is overblown. What is not overblown is the structural "
        "pressure now bearing down on every services business that prices value by the hour. "
        "The single largest use case for LLMs today is software engineering itself — "
        "which puts direct pressure on industries built around writing software with people. "
        "Nearly 50% of the workforce that drives value in this next era will come from "
        "non-STEM disciplines. That is the talent architecture of A3. "
        "The most important innovation of the coming decade will not come from artificial "
        "intelligence. It will come from empowering every worker to use it to generate "
        "economic and societal value."
    )

    PRESS_RELEASE_SAMPLE = (
        "Today, Cognizant announced a strategic acquisition that advances our position "
        "as an AI builder company. As I call it, this is the verification economy taking "
        "shape — where outcome-based delivery replaces labor-based models. "
        "We are building intelligence, not just systems, and this partnership accelerates "
        "our ability to deliver measurable outcomes for our clients."
    )

    FAIL_SAMPLE = (
        "# The Future of IT Services\n"
        "We need to leverage our synergies and utilize best-in-class paradigm shifts "
        "to move the needle on transformative outcomes."
    )

    tool = EditorialGateTool()

    print("\n" + "="*60)
    print("TEST 1 — BLOG (EXPECTED PASS)")
    print("="*60)
    result = tool.invoke({"candidate_text": BLOG_SAMPLE, "content_type": "blog"})
    print(json.dumps(result, indent=2))

    print("\n" + "="*60)
    print("TEST 2 — PRESS RELEASE (EXPECTED PASS)")
    print("="*60)
    result = tool.invoke({"candidate_text": PRESS_RELEASE_SAMPLE, "content_type": "press_release"})
    print(json.dumps(result, indent=2))

    print("\n" + "="*60)
    print("TEST 3 — EXPECTED FAIL")
    print("="*60)
    result = tool.invoke({"candidate_text": FAIL_SAMPLE, "content_type": "blog"})
    print(json.dumps(result, indent=2))
