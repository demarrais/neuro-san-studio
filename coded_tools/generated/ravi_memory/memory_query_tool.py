"""Chroma-backed memory query and state-management tool for rAvI."""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from neuro_san.interfaces.coded_tool import CodedTool

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHROMA_PATH = os.environ.get("RAVI_CHROMA_PATH", "./ravi_chroma_db")
NOT_FOUND = {"status": "NOT_FOUND"}

_clients: dict[str, Any] = {}


def _normalize_path(path: str | None = None) -> str:
    normalized = Path(path or _CHROMA_PATH).expanduser()
    if not normalized.is_absolute():
        normalized = _REPO_ROOT / normalized
    return str(normalized.resolve())


def _get_client(path: str | None = None) -> Any:
    client_path = _normalize_path(path)
    if client_path not in _clients:
        _clients[client_path] = chromadb.PersistentClient(
            path=client_path,
            settings=Settings(anonymized_telemetry=False),
        )
        logger.info("MemoryQueryTool: PersistentClient at %s", client_path)
    return _clients[client_path]


def _col(name: str, path: str | None = None) -> Any:
    return _get_client(path).get_or_create_collection(name=name)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryQueryTool(CodedTool):
    """Read and write rAvI memory collections."""

    _VERSION = "v4-20261124-explicit-lane-paths"

    def invoke(
        self,
        args: dict[str, Any],
        sly_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del sly_data
        payload = self._unwrap_args(args)
        if "query" in payload and "operation" not in payload:
            return self._query(
                query=payload.get("query", ""),
                collection=payload.get("collection", "ravi_voice_knowledge"),
                top_k=payload.get("top_k", 5),
                path=payload.get("path"),
            )

        operation = payload.get("operation", "query")
        function = {
            "health_check": self._health_check,
            "query": self._query_from_args,
            "search": self._query_from_args,
            "query_voice_knowledge": self._query_from_args,
            "get_content_ledger": self._get_content_ledger,
            "get_voice_profile": self._get_voice_profile,
            "upsert_voice_profile": self._upsert_voice_profile,
            "query_knowledge_graph": self._query_knowledge_graph,
            "add_knowledge_entry": self._add_knowledge_entry,
            "log_session_event": self._log_session_event,
            "log_ingested_content": self._log_ingested_content,
        }.get(operation)
        if function is None:
            return {"success": False, "error": f"Unknown operation: {operation}"}
        try:
            return function(
                **{
                    key: value
                    for key, value in payload.items()
                    if key != "operation"
                }
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.exception("Memory operation failed: %s", operation)
            return {"success": False, "error": str(exc)}

    async def async_invoke(
        self,
        args: dict[str, Any],
        sly_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(self.invoke, args, sly_data)

    @staticmethod
    def _unwrap_args(args: Any) -> dict[str, Any]:
        if not isinstance(args, dict):
            return {}

        tool_args = args.get("tool_args")
        if isinstance(tool_args, dict):
            inner = tool_args.get("args")
            if isinstance(inner, list) and inner and isinstance(inner[0], dict):
                return dict(inner[0])
            if isinstance(inner, dict) and inner:
                return dict(inner)
            stripped = {
                key: value
                for key, value in tool_args.items()
                if key
                not in {
                    "args",
                    "origin",
                    "origin_str",
                    "tool_start",
                    "progress_reporter",
                }
            }
            if stripped:
                return stripped

        inner_args = args.get("args")
        if isinstance(inner_args, dict):
            return dict(inner_args)
        return dict(args)

    def _query_from_args(self, **kwargs: Any) -> dict[str, Any]:
        return self._query(
            query=kwargs.get("query", ""),
            collection=kwargs.get("collection", "ravi_voice_knowledge"),
            top_k=kwargs.get("top_k", 5),
            path=kwargs.get("path"),
        )

    def _query(
        self,
        query: str = "",
        collection: str = "ravi_voice_knowledge",
        top_k: int = 5,
        path: str | None = None,
    ) -> dict[str, Any]:
        if not query:
            return {"status": "ERROR", "error": "query is required"}

        client_path = _normalize_path(path)
        collection_handle = _col(collection, client_path)
        count = collection_handle.count()
        if count == 0:
            return {
                "status": "EMPTY",
                "documents": [],
                "count": 0,
                "collection": collection,
                "path": client_path,
                "warning": (
                    f"Collection '{collection}' is empty. Ingest content first."
                ),
            }

        try:
            requested_top_k = max(1, int(top_k))
        except (TypeError, ValueError):
            requested_top_k = 5
        results = collection_handle.query(
            query_texts=[query],
            n_results=min(requested_top_k, count),
            include=["documents", "metadatas", "distances"],
        )
        documents = [
            {
                "id": record_id,
                "content": document,
                "metadata": metadata,
                "relevance": round(1 - distance, 4),
            }
            for record_id, document, metadata, distance in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]
        logger.info(
            "query: path='%s' collection='%s' hits=%d",
            client_path,
            collection,
            len(documents),
        )
        return {
            "status": "OK",
            "documents": documents,
            "count": len(documents),
            "collection": collection,
            "path": client_path,
        }

    def _health_check(
        self,
        path: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        try:
            client_path = _normalize_path(path)
            client = _get_client(client_path)
            collections = [
                collection.name for collection in client.list_collections()
            ]
            return {
                "status": "OK",
                "collections": collections,
                "path": client_path,
                "timestamp": _now(),
            }
        except Exception as exc:  # pylint: disable=broad-exception-caught
            return {
                "status": "ERROR",
                "error": str(exc),
                "path": _normalize_path(path),
                "timestamp": _now(),
            }

    def _get_content_ledger(self, **_: Any) -> dict[str, Any]:
        collection = _col("content_ledger")
        results = collection.get(include=["metadatas", "documents"])
        if not results["ids"]:
            return {"status": "OK", "records": [], "count": 0}
        return {
            "status": "OK",
            "count": len(results["ids"]),
            "records": [
                {
                    "id": record_id,
                    "metadata": metadata,
                    "summary": document,
                }
                for record_id, metadata, document in zip(
                    results["ids"],
                    results["metadatas"],
                    results["documents"],
                )
            ],
        }

    def _get_voice_profile(self, **_: Any) -> dict[str, Any]:
        collection = _col("voice_profile")
        results = collection.get(
            ids=["current_profile"],
            include=["documents", "metadatas"],
        )
        if not results["ids"]:
            return NOT_FOUND
        try:
            profile = json.loads(results["documents"][0])
        except json.JSONDecodeError:
            profile = {"raw": results["documents"][0]}
        metadata = results["metadatas"][0]
        return {
            "status": "OK",
            "profile": profile,
            "version": metadata.get("version", 1),
            "updated_at": metadata.get("updated_at", "unknown"),
        }

    def _upsert_voice_profile(
        self,
        voice_signature: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        if not voice_signature:
            return {"success": False, "error": "voice_signature is required"}
        collection = _col("voice_profile")
        existing = self._get_voice_profile()
        version = 1 if existing == NOT_FOUND else existing.get("version", 1) + 1
        merged = (
            voice_signature
            if existing == NOT_FOUND
            else _deep_merge(existing["profile"], voice_signature)
        )
        collection.upsert(
            ids=["current_profile"],
            documents=[json.dumps(merged)],
            metadatas=[{"version": version, "updated_at": _now()}],
        )
        return {"success": True, "version": version, "updated_at": _now()}

    def _query_knowledge_graph(
        self,
        topic: str = "",
        top_k: int = 5,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self._query(
            query=topic,
            collection="knowledge_graph",
            top_k=top_k,
            path=kwargs.get("path"),
        )

    def _add_knowledge_entry(
        self,
        summary: str = "",
        source_url: str = "",
        source_title: str = "",
        relevance_score: float = 0.0,
        credibility_score: float = 0.0,
        key_claims: list[Any] | None = None,
        contradicts_author: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        record_id = f"kg_{uuid.uuid4().hex[:12]}"
        metadata = {
            "source_url": source_url,
            "source_title": source_title,
            "relevance_score": relevance_score,
            "credibility_score": credibility_score,
            "key_claims": json.dumps(key_claims or []),
            "contradicts_author": str(contradicts_author),
            "added_at": _now(),
        }
        _col("knowledge_graph").add(
            ids=[record_id],
            documents=[summary],
            metadatas=[metadata],
        )
        return {"success": True, "record_id": record_id}

    def _log_session_event(
        self,
        event_type: str = "generation",
        topic: str = "",
        format: str = "",
        composite_score: float = 0.0,
        draft_length: int = 0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        record_id = f"session_{uuid.uuid4().hex[:12]}"
        _col("session_log").add(
            ids=[record_id],
            documents=[topic],
            metadatas=[
                {
                    "event_type": event_type,
                    "topic": topic,
                    "format": format,
                    "composite_score": composite_score,
                    "draft_length": draft_length,
                    "logged_at": _now(),
                }
            ],
        )
        return {"success": True, "record_id": record_id}

    def _log_ingested_content(
        self,
        source_url: str = "",
        source_type: str = "unknown",
        title: str = "",
        word_count: int = 0,
        platform: str = "",
        summary: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        record_id = f"ledger_{uuid.uuid4().hex[:12]}"
        metadata = {
            "source_url": source_url,
            "source_type": source_type,
            "title": title,
            "word_count": word_count,
            "platform": platform,
            "ingested_at": _now(),
        }
        _col("content_ledger").add(
            ids=[record_id],
            documents=[summary or title],
            metadatas=[metadata],
        )
        return {"success": True, "record_id": record_id}


def _deep_merge(
    base: dict[str, Any],
    update: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(base)
    for key, value in update.items():
        if key not in merged:
            merged[key] = value
        elif isinstance(value, list) and isinstance(merged[key], list):
            seen: set[str] = set()
            combined: list[Any] = []
            for item in merged[key] + value:
                item_key = (
                    item
                    if isinstance(item, str)
                    else json.dumps(item, sort_keys=True)
                )
                if item_key not in seen:
                    seen.add(item_key)
                    combined.append(item)
            merged[key] = combined
        elif isinstance(value, (int, float)) and isinstance(
            merged[key],
            (int, float),
        ):
            merged[key] = round((merged[key] + value) / 2, 2)
        else:
            merged[key] = value
    return merged
