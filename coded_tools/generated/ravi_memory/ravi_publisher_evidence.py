"""Evidence-packet construction and dynamic numeric grounding for rAvI."""

import re
from datetime import datetime
from datetime import timezone
from typing import Any

from coded_tools.generated.ravi_memory.ravi_publisher_support import AUTHENTIC_VOICE_COLLECTION
from coded_tools.generated.ravi_memory.ravi_publisher_support import MAX_PACKET_EXCERPT_CHARS
from coded_tools.generated.ravi_memory.ravi_publisher_support import MAX_SOURCE_CHARS
from coded_tools.generated.ravi_memory.ravi_publisher_support import TOPIC_EVIDENCE_COLLECTION

_NUMERIC_TOKEN_PATTERN = re.compile(
    r"(?<![\w])(?:"
    r"(?:\$\s?|USD\s?|EUR\s?|GBP\s?)\d[\d,]*(?:\.\d+)?"
    r"(?:\s?(?:trillion|billion|million|thousand|[TMBK]))?"
    r"|\d[\d,]*(?:\.\d+)?\s?(?:%|percent|percentage points?)"
    r"|\d[\d,]*(?:\.\d+)?\s?"
    r"(?:basis points?|bps|trillion|billion|million|thousand|[xX])"
    r"|\d[\d,]*(?:\.\d+)?"
    r")(?![\w])",
    flags=re.IGNORECASE,
)


def document_content(document: dict[str, Any]) -> str:
    content = document.get("content", "") if isinstance(document, dict) else ""
    return str(content).strip()


def deduplicate_documents(documents: Any) -> list[dict[str, Any]]:
    if not isinstance(documents, list):
        return []
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for document in documents:
        normalized = (
            dict(document) if isinstance(document, dict) else {"content": str(document)}
        )
        content = document_content(normalized)
        key = str(normalized.get("id") or content)
        if content and key not in seen:
            seen.add(key)
            unique.append(normalized)
    return unique


def normalize_numeric_token(token: str) -> str:
    return re.sub(r"\s+", " ", token.strip().lower())


def ordered_numeric_tokens(text: str) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for match in _NUMERIC_TOKEN_PATTERN.finditer(text or ""):
        token = match.group(0).strip()
        normalized = normalize_numeric_token(token)
        if normalized and normalized not in seen:
            seen.add(normalized)
            ordered.append(token)
    return ordered


def unsupported_numeric_tokens(
    draft: str,
    allowed_tokens: list[str],
) -> list[str]:
    allowed = {normalize_numeric_token(token) for token in allowed_tokens}
    unsupported: list[str] = []
    seen: set[str] = set()
    for token in ordered_numeric_tokens(draft):
        normalized = normalize_numeric_token(token)
        if normalized not in allowed and normalized not in seen:
            seen.add(normalized)
            unsupported.append(token)
    return unsupported


def add_numeric_grounding_failure(
    gate_report: dict[str, Any],
    unsupported_numbers: list[str],
) -> dict[str, Any]:
    report = dict(gate_report)
    checks = list(report.get("checks") or [])
    failed_checks = list(report.get("failed_checks") or [])
    violations = list(report.get("violations") or [])
    message = (
        "UNSUPPORTED NUMBERS: "
        f"{', '.join(unsupported_numbers)}. "
        "Use only exact numeric tokens from the evidence packet."
    )
    checks.append(
        {
            "passed": False,
            "check": "evidence_numeric_grounding",
            "unsupported_numbers": unsupported_numbers,
            "message": message,
        }
    )
    if "evidence_numeric_grounding" not in failed_checks:
        failed_checks.append("evidence_numeric_grounding")
    violations.append(message)
    report.update(
        {
            "gate_passed": False,
            "status": "GATE_FAILURE",
            "checks": checks,
            "failed_checks": failed_checks,
            "violations": violations,
            "failed_count": len(failed_checks),
        }
    )
    return report


def format_documents(documents: list[dict[str, Any]], prefix: str) -> str:
    formatted: list[str] = []
    for index, document in enumerate(documents, start=1):
        metadata = (
            document.get("metadata")
            if isinstance(document.get("metadata"), dict)
            else {}
        )
        source = (
            metadata.get("source")
            or metadata.get("source_title")
            or metadata.get("file_name")
            or metadata.get("title")
            or "unknown"
        )
        content = document_content(document)[:MAX_SOURCE_CHARS]
        formatted.append(f"[{prefix}{index}] source={source}\n{content}")
    return "\n\n".join(formatted)


def format_user_supplied(canonical_facts: str, source_material: str) -> str:
    blocks: list[str] = []
    if canonical_facts:
        blocks.append(
            "[U1] caller-supplied canonical facts\n"
            f"{canonical_facts[:MAX_SOURCE_CHARS]}"
        )
    if source_material:
        source_id = len(blocks) + 1
        blocks.append(
            f"[U{source_id}] caller-supplied source material\n"
            f"{source_material[:MAX_SOURCE_CHARS]}"
        )
    return "\n\n".join(blocks) or "No user-supplied factual material."


def _packet_sources(
    documents: list[dict[str, Any]],
    prefix: str,
) -> list[dict[str, Any]]:
    packet_sources: list[dict[str, Any]] = []
    for index, document in enumerate(documents, start=1):
        metadata = (
            document.get("metadata")
            if isinstance(document.get("metadata"), dict)
            else {}
        )
        content = document_content(document)
        grounding_content = content[:MAX_SOURCE_CHARS]
        packet_sources.append(
            {
                "source_id": f"{prefix}{index}",
                "memory_id": document.get("id"),
                "relevance": document.get("relevance"),
                "source": (
                    metadata.get("source")
                    or metadata.get("source_title")
                    or metadata.get("file_name")
                    or metadata.get("title")
                ),
                "source_url": metadata.get("source_url") or metadata.get("url"),
                "speaker": metadata.get("speaker"),
                "authorship": (
                    metadata.get("authorship") or metadata.get("author")
                ),
                "content_type": (
                    metadata.get("content_type") or metadata.get("type")
                ),
                "quotability": metadata.get("quotability"),
                "external_use": metadata.get("external_use"),
                "excerpt": grounding_content[:MAX_PACKET_EXCERPT_CHARS],
                "numeric_tokens": ordered_numeric_tokens(grounding_content),
            }
        )
    return packet_sources


def build_evidence_packet(
    request: str,
    content_type: str,
    authentic_voice_path: str,
    topic_evidence_path: str,
    voice_documents: list[dict[str, Any]],
    evidence_documents: list[dict[str, Any]],
    canonical_facts: str,
    source_material: str,
    voice_warning: str | None,
    evidence_warning: str | None,
) -> dict[str, Any]:
    numeric_sources = [
        document_content(document)[:MAX_SOURCE_CHARS]
        for document in evidence_documents
    ]
    numeric_sources.extend(
        [
            canonical_facts[:MAX_SOURCE_CHARS],
            source_material[:MAX_SOURCE_CHARS],
        ]
    )
    allowed_numeric_tokens = ordered_numeric_tokens(
        "\n".join(filter(None, numeric_sources))
    )

    gaps: list[str] = []
    if not voice_documents:
        gaps.append(
            "No authentic-voice matches were retrieved from "
            f"{AUTHENTIC_VOICE_COLLECTION}."
        )
    if not evidence_documents and not canonical_facts and not source_material:
        gaps.append(
            "No topic evidence was retrieved from "
            f"{TOPIC_EVIDENCE_COLLECTION} or supplied by the caller."
        )
    if voice_warning:
        gaps.append(voice_warning)
    if evidence_warning:
        gaps.append(evidence_warning)

    user_supplied: list[dict[str, Any]] = []
    if canonical_facts:
        user_supplied.append(
            {
                "source_id": "U1",
                "source_type": "canonical_facts",
                "verification_status": "caller_supplied",
                "excerpt": canonical_facts[:MAX_PACKET_EXCERPT_CHARS],
                "numeric_tokens": ordered_numeric_tokens(
                    canonical_facts[:MAX_SOURCE_CHARS]
                ),
            }
        )
    if source_material:
        user_supplied.append(
            {
                "source_id": f"U{len(user_supplied) + 1}",
                "source_type": "source_material",
                "verification_status": "caller_supplied",
                "excerpt": source_material[:MAX_PACKET_EXCERPT_CHARS],
                "numeric_tokens": ordered_numeric_tokens(
                    source_material[:MAX_SOURCE_CHARS]
                ),
            }
        )

    return {
        "request": request,
        "content_type": content_type,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "lanes": {
            "authentic_voice": {
                "collection": AUTHENTIC_VOICE_COLLECTION,
                "path": authentic_voice_path,
                "role": "style_only",
                "matches": _packet_sources(voice_documents, "V"),
            },
            "topic_evidence": {
                "collection": TOPIC_EVIDENCE_COLLECTION,
                "path": topic_evidence_path,
                "role": "factual_support",
                "matches": _packet_sources(evidence_documents, "E"),
            },
            "user_supplied": {
                "role": "factual_support",
                "matches": user_supplied,
            },
        },
        "allowed_numeric_tokens": allowed_numeric_tokens,
        "gaps": gaps,
        "policy": {
            "general_knowledge_fallback": False,
            "voice_lane_can_supply_facts": False,
            "unsupported_numbers_are_gate_failures": True,
        },
    }


def empty_evidence_packet(request: str) -> dict[str, Any]:
    return {
        "request": request,
        "content_type": None,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "lanes": {},
        "allowed_numeric_tokens": [],
        "gaps": ["No request was supplied."],
        "policy": {
            "general_knowledge_fallback": False,
            "voice_lane_can_supply_facts": False,
            "unsupported_numbers_are_gate_failures": True,
        },
    }
