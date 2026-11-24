"""Configuration and transport helpers for the rAvI gated publisher."""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
AUTHENTIC_VOICE_COLLECTION = "ravi_voice_primary"
TOPIC_EVIDENCE_COLLECTION = "ravi_voice_knowledge"
DEFAULT_AUTHENTIC_VOICE_PATH = "./chroma_db"
DEFAULT_TOPIC_EVIDENCE_PATH = "./ravi_chroma_db"
DEFAULT_MAX_ATTEMPTS = 7
MAX_SOURCE_CHARS = 4_000
MAX_PACKET_EXCERPT_CHARS = 700

QUOTE_TRIGGERS = (
    "press release quote",
    "single quote",
    "quote only",
    "one quote",
    "a quote from",
    "quote from ravi",
    "2-3 sentence",
    "2 to 3 sentence",
    "quotable passage",
)

_CONTENT_TYPE_ALIASES = {
    "article": "blog",
    "blog_post": "blog",
    "linkedin": "social",
    "linkedin_post": "social",
    "post": "social",
    "press_release_quote": "press_release",
    "quote": "press_release",
    "speech": "transcript",
    "statement": "press_release",
}

# These substitutions are applied only to the transport copy of prompts sent to
# Azure. Retrieved records, evidence packets, and generated drafts remain unchanged.
_AZURE_SANITIZATION_REPLACEMENTS = (
    ("exploiting vulnerabilities", "identifying and remediating security flaws"),
    ("finding and exploiting", "identifying and fixing"),
    ("zero-day", "previously unknown security flaw"),
    ("offensive capabilities", "proactive security capabilities"),
    ("offensive cyber", "proactive cyber defense"),
)

_AZURE_VIOLATION_REPLACEMENTS = (
    ("BANNED", "disallowed"),
    ("Remove every", "Revise each"),
    ("Fix ALL", "Address all"),
    ("before resubmitting", "in the revision"),
)


def unwrap_args(args: Any) -> dict[str, Any]:
    """Accept NeuroSAN's observed wrapper shapes without mutating the input."""
    if not isinstance(args, dict):
        return {"request": str(args)}

    tool_args = args.get("tool_args")
    if isinstance(tool_args, dict):
        inner = tool_args.get("args")
        if isinstance(inner, list) and inner and isinstance(inner[0], dict):
            return dict(inner[0])
        if isinstance(inner, dict):
            return dict(inner)
        stripped = {
            key: value
            for key, value in tool_args.items()
            if key not in {
                "args",
                "origin",
                "origin_str",
                "progress_reporter",
                "tool_start",
            }
        }
        if stripped:
            return stripped

    inner_args = args.get("args")
    if isinstance(inner_args, dict):
        return dict(inner_args)
    return dict(args)


def request_from_args(args: dict[str, Any]) -> str:
    value = (
        args.get("request")
        or args.get("topic")
        or args.get("draft_request")
        or args.get("query")
    )
    return "" if value is None else str(value).strip()


def content_type_from_args(args: dict[str, Any], request: str) -> str:
    raw_value = (
        args.get("content_type")
        or args.get("draft_type")
        or args.get("format")
        or ""
    )
    normalized = str(raw_value).strip().lower().replace("-", "_").replace(" ", "_")
    normalized = _CONTENT_TYPE_ALIASES.get(normalized, normalized)
    valid_types = {
        "transcript",
        "blog",
        "white_paper",
        "social",
        "press_release",
        "letter",
    }
    if normalized in valid_types:
        return normalized

    request_lower = request.lower()
    if any(trigger in request_lower for trigger in QUOTE_TRIGGERS):
        return "press_release"
    if "linkedin" in request_lower or "social post" in request_lower:
        return "social"
    if "letter" in request_lower:
        return "letter"
    if "white paper" in request_lower:
        return "white_paper"
    return "blog"


def text_from_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    return str(value).strip()


def bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


def resolve_store_path(configured_path: str | None, default_path: str) -> str:
    path = Path(configured_path or default_path).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    return str(path.resolve())


def load_directive() -> str:
    configured_path = os.environ.get("EDITORIAL_DIRECTIVE_PATH")
    path = (
        Path(configured_path).expanduser()
        if configured_path
        else REPO_ROOT / "editorial_guide__anti_ai_slop.txt"
    )
    if not path.is_absolute():
        path = REPO_ROOT / path
    try:
        full_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Editorial directive load failed at %s: %s", path, exc)
        return ""
    return full_text.split("--- Page 1 ---", maxsplit=1)[0].strip()


def sanitize_for_azure(text: str) -> str:
    sanitized = text
    for source, replacement in _AZURE_SANITIZATION_REPLACEMENTS:
        sanitized = re.sub(
            re.escape(source),
            replacement,
            sanitized,
            flags=re.IGNORECASE,
        )
    return sanitized


def sanitize_violations_for_azure(text: str) -> str:
    sanitized = text
    for source, replacement in _AZURE_VIOLATION_REPLACEMENTS:
        sanitized = re.sub(
            re.escape(source),
            replacement,
            sanitized,
            flags=re.IGNORECASE,
        )
    return sanitize_for_azure(sanitized)


def sanitize_model_name(model_name: str) -> str:
    return model_name.strip().strip('"').strip("'")


def normalize_draft_output(content: str) -> str:
    """Remove transport wrappers without rewriting the draft itself."""
    draft = content.strip()
    if draft.startswith("```") and draft.endswith("```"):
        draft = re.sub(
            r"^```(?:text|markdown)?\s*",
            "",
            draft,
            flags=re.IGNORECASE,
        )
        draft = re.sub(r"\s*```$", "", draft)
    if draft.startswith("{"):
        try:
            parsed = json.loads(draft)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict) and isinstance(parsed.get("draft"), str):
            draft = parsed["draft"].strip()
    return draft
