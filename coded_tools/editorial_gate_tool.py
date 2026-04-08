"""
editorial_gate_tool.py

EditorialGateTool for the Ravi Kumar S digital twin.
Enforces voice fidelity, editorial quality, and semantic similarity
against the verbatim transcript stored in ChromaDB (ravi_voice_primary).

Neuro SAN coded tool — invoke via agent network or CLI test harness.
"""

import json
import os
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
SIMILARITY_THRESHOLD = 0.75   # cosine distance ceiling (lower = more similar)
TOP_K_CHUNKS         = 3      # chunks to retrieve for scoring

# Banned words — violate Ravi's voice standards
BANNED_WORDS = [
    "utilize", "synergy", "synergize", "holistic", "ecosystem",
    "bandwidth", "circle back", "deep dive", "boil the ocean",
    "move the needle", "low-hanging fruit", "paradigm shift", "value-add",
    "learnings", "ideate", "socialize", "democratize", "empower",
    "transformative", "game-changer", "revolutionary",
    "cutting-edge", "best-in-class", "world-class", "robust",
    "actionable insights", "thought leader", "pivot",
]

# Required opener signals — first 150 chars must contain at least one
OPENER_SIGNALS = [
    "i mean", "you know", "um,", "uh,", "the reality is",
    "i would say", "look,", "here's the thing", "let me",
    "if you reflect", "i actually", "i think",
]

# Required closer signals — last 150 chars must contain at least one
CLOSER_SIGNALS = [
    "so", "and that is", "that is the", "which means", "therefore",
    "because", "if we can", "only if", "the ones who", "that's the power",
    "that is the power",
]

# Attribution framing — Ravi's way of owning ideas
ATTRIBUTION_PHRASES = [
    "as i call it", "as we call it", "i've written", "i've spoken",
    "what i mean by", "in my", "we call it", "i would say",
    "i mean,", "you know,", "i have spoken",
]

# Framework vocabulary — outputs should use at least 2
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


def check_opener_quality(text: str) -> dict:
    first_150 = text[:150].lower()
    found = [s for s in OPENER_SIGNALS if s in first_150]
    passed = len(found) > 0
    return {
        "passed": passed,
        "check": "opener_quality",
        "signals_found": found,
        "message": (
            "Opener has authentic Ravi voice signal."
            if passed else
            "Opener lacks spoken cadence. Should open naturally: 'I mean,', 'You know,', "
            "'The reality is...', 'I would say...'"
        ),
    }


def check_closer_quality(text: str) -> dict:
    last_150 = text[-150:].lower()
    found = [s for s in CLOSER_SIGNALS if s in last_150]
    passed = len(found) > 0
    return {
        "passed": passed,
        "check": "closer_quality",
        "signals_found": found,
        "message": (
            "Closer lands with valid wrap-up signal."
            if passed else
            "Closer is weak. Should end declaratively: 'That is the power of...', "
            "'And only if we...', 'Which means...'"
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
            f"Output should use at least 2 of Ravi's established vocabulary "
            f"(e.g. 'digital labor', 'AI builder', 'context engineering', '1st principles')."
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
            "'as we call it', 'what I mean by', 'I've spoken about this' "
            "to anchor his original ideas."
        ),
    }


def check_header_structure(text: str) -> dict:
    """
    Ravi speaks in flowing prose with verbal numbering — not markdown headers.
    Flag any output that uses # headers.
    """
    lines = text.split("\n")
    header_lines = [l.strip() for l in lines if l.strip().startswith("#")]
    passed = len(header_lines) == 0
    return {
        "passed": passed,
        "check": "header_structure",
        "header_lines_found": header_lines,
        "message": (
            "No markdown headers — correct spoken-word format."
            if passed else
            f"Output contains markdown headers which break voice fidelity. "
            f"Ravi numbers points verbally, not as headers. Found: {header_lines}"
        ),
    }


def check_semantic_similarity(text: str) -> dict:
    """
    Query ChromaDB ravi_voice_primary for nearest transcript chunks.
    Score = average cosine distance across top-k results.
    Lower distance = more semantically aligned with Ravi's actual voice.
    """
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
                "chunk_id": m["chunk_id"],
                "topic":    m["topic"],
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
                f"Semantic similarity OK — avg cosine distance {avg_distance:.4f} "
                f"within threshold {SIMILARITY_THRESHOLD}."
                if passed else
                f"Semantic drift detected — avg cosine distance {avg_distance:.4f} "
                f"exceeds threshold {SIMILARITY_THRESHOLD}. "
                f"Output is not semantically grounded in Ravi's verbatim voice."
            ),
        }

    except Exception as e:
        return {
            "passed": False,
            "check": "semantic_similarity",
            "error": str(e),
            "message": f"ChromaDB query failed: {e}. Ensure chroma_db is present at {CHROMA_DB_PATH}.",
        }



def check_statistics(text: str) -> dict:
    import re
    found = re.findall(r"\d+\.?\d*\s*%|\d+\.?\d*x\b|\d{4}\s*occupations|\d+,\d+\s*tasks|\d+\s*professions", text.lower())
    passed = len(found) >= 2
    return {
        "passed": passed,
        "check": "statistics",
        "stats_found": found,
        "message": (
            f"Statistics present: {found}"
            if passed else
            "MISSING STATISTICS: Include at least 2 data points from ingested corpus. "
            "Available: 93% job exposure, 4.5x exposure rate, 31%->7% minimal exposure, "
            "60% occupations didn't exist in 1940, 2.2% productivity growth 2025, "
            "4.4% unemployment Feb 2026."
        ),
    }


def check_em_dashes(text: str) -> dict:
    import re
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

# ── Main Gate Orchestrator ────────────────────────────────────────────────────

class EditorialGateTool:
    """
    Neuro SAN coded tool.
    Pass any candidate output through all editorial gates.
    Returns structured pass/fail report with per-check detail.
    """

    def get_tool_name(self) -> str:
        return "editorial_gate_tool"

    def get_instructions(self) -> str:
        return (
            "Evaluate any candidate output for voice fidelity and editorial quality "
            "before it is returned to the user. Pass the full candidate text as "
            "'candidate_text'. The tool returns a structured gate report. "
            "If gate_passed is False, revise the output to address failed_checks "
            "before finalizing."
        )

    def get_args_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "candidate_text": {
                    "type": "string",
                    "description": "Full candidate output text to evaluate against all gates.",
                }
            },
            "required": ["candidate_text"],
        }

    def invoke(self, args: dict[str, Any]) -> dict[str, Any]:
        candidate_text = args.get("candidate_text", "")

        if not candidate_text.strip():
            return {
                "gate_passed": False,
                "error": "candidate_text is empty.",
                "checks": [],
            }

        checks = [
            check_banned_words(candidate_text),
            check_opener_quality(candidate_text),
            check_closer_quality(candidate_text),
            check_framework_vocabulary(candidate_text),
            check_attribution_framing(candidate_text),
            check_header_structure(candidate_text),
            check_semantic_similarity(candidate_text),
            check_statistics(candidate_text),
            check_em_dashes(candidate_text),
        ]

        failed = [c for c in checks if not c["passed"]]
        passed = [c for c in checks if c["passed"]]
        gate_passed = len(failed) == 0

        return {
            "gate_passed": gate_passed,
            "total_checks": len(checks),
            "passed_count": len(passed),
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

    PASS_SAMPLE = (
        "I mean, the reality is, we are moving from system integrators to AI builders, "
        "as I call it. And what that means, you know, is the role of context engineering "
        "becomes central. You are not just building systems — you are infusing digital labor "
        "into the operations of enterprises. That is the 1st principles shift. "
        "And only if we reforge those principles will this industry generate durable, "
        "sustainable value. That is the power of what this moment demands."
    )

    FAIL_SAMPLE = (
        "# The Future of IT Services\n"
        "We need to leverage our synergies and utilize best-in-class paradigm shifts "
        "to move the needle on transformative outcomes. Our robust ecosystem will "
        "empower thought leaders to pivot toward actionable insights."
    )

    tool = EditorialGateTool()

    print("\n" + "="*60)
    print("TEST 1 — EXPECTED PASS")
    print("="*60)
    result = tool.invoke({"candidate_text": PASS_SAMPLE})
    print(json.dumps(result, indent=2))

    print("\n" + "="*60)
    print("TEST 2 — EXPECTED FAIL")
    print("="*60)
    result = tool.invoke({"candidate_text": FAIL_SAMPLE})
    print(json.dumps(result, indent=2))
