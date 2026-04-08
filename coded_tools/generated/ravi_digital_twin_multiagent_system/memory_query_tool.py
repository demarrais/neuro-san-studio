"""
memory_query_tool.py  —  ChromaDB-backed persistent store for rAvI.

FIX SUMMARY
-----------
1. health_check() operation added — called by memory_layer_manager on startup.
   Returns explicit OK/ERROR so the system can abort before silently failing.
2. All write operations now return {success, record_id, error} explicitly.
   They RAISE on connection failure rather than swallowing exceptions.
3. Reads return NOT_FOUND sentinel instead of None so callers can distinguish
   "empty result" from "store unreachable".
4. Module-level _get_client() validates the connection once and caches it;
   subsequent calls reuse the validated client.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

# ── connection config ────────────────────────────────────────────────────────
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
CHROMA_PERSIST_DIR = "./ravi_chroma_db"   # used for local persistent client

# Collection names
COL_CONTENT_LEDGER  = "content_ledger"
COL_VOICE_PROFILE   = "voice_profile"
COL_KNOWLEDGE_GRAPH = "knowledge_graph"
COL_SESSION_LOG     = "session_log"

NOT_FOUND = {"status": "NOT_FOUND"}

# ── singleton client ─────────────────────────────────────────────────────────
_client: Any = None  # chromadb.ClientAPI instance


def _get_client() -> Any:
    """Return a validated ChromaDB client, raising on failure.
    Uses HttpClient to match chroma_bootstrap.py — ChromaDB must be
    running before the agent network starts:
        chroma run --path ./ravi_chroma_db
    """
    global _client
    if _client is not None:
        return _client
    try:
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=Settings(anonymized_telemetry=False),
        )
        # Validate by heartbeat — will raise if server is unreachable.
        client.heartbeat()
        _client = client
        logger.info("ChromaDB HttpClient connected at %s:%s", CHROMA_HOST, CHROMA_PORT)
        return _client
    except Exception as exc:
        logger.error("ChromaDB connection FAILED: %s", exc)
        raise RuntimeError(
            f"ChromaDB unavailable at {CHROMA_HOST}:{CHROMA_PORT}. "
            f"Run: chroma run --path ./ravi_chroma_db — then restart the agent network. "
            f"Error: {exc}"
        ) from exc


def _col(name: str):
    """Get or create a named collection."""
    return _get_client().get_or_create_collection(name=name)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── MemoryQueryTool class ────────────────────────────────────────────────────

class MemoryQueryTool:
    """
    NeuroSAN tool class.  The framework instantiates this and calls
    run(operation, **kwargs) for each agent invocation.
    """

    def run(self, operation: str, **kwargs) -> dict[str, Any]:
        dispatch = {
            "health_check":         self.health_check,
            "get_content_ledger":   self.get_content_ledger,
            "log_ingested_content": self.log_ingested_content,
            "get_voice_profile":    self.get_voice_profile,
            "upsert_voice_profile": self.upsert_voice_profile,
            "query_knowledge_graph":self.query_knowledge_graph,
            "add_knowledge_entry":  self.add_knowledge_entry,
            "log_session_event":    self.log_session_event,
        }
        fn = dispatch.get(operation)
        if fn is None:
            return {"success": False, "error": f"Unknown operation: {operation}"}
        try:
            return fn(**kwargs)
        except RuntimeError as exc:
            # Connection-level failure — surface clearly.
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.exception("memory_query_tool error in %s", operation)
            return {"success": False, "error": f"Unexpected error: {exc}"}

    # ── FIX 1: health_check ─────────────────────────────────────────────────
    def health_check(self) -> dict:
        """
        Validate ChromaDB is reachable and return collection inventory.
        Called by memory_layer_manager on every startup before any ingestion.
        """
        try:
            client = _get_client()
            client.heartbeat()
            cols = [c.name for c in client.list_collections()]
            return {
                "status": "OK",
                "collections": cols,
                "host": CHROMA_HOST,
                "port": CHROMA_PORT,
                "timestamp": _now(),
            }
        except Exception as exc:
            return {
                "status": "ERROR",
                "error": str(exc),
                "hint": f"Run: chroma run --path ./ravi_chroma_db",
                "timestamp": _now(),
            }

    # ── Content Ledger ───────────────────────────────────────────────────────
    def get_content_ledger(self) -> dict:
        col = _col(COL_CONTENT_LEDGER)
        results = col.get(include=["metadatas", "documents"])
        if not results["ids"]:
            return {"status": "OK", "records": [], "count": 0}
        records = [
            {"id": rid, "metadata": meta, "summary": doc}
            for rid, meta, doc in zip(
                results["ids"], results["metadatas"], results["documents"]
            )
        ]
        return {"status": "OK", "records": records, "count": len(records)}

    def log_ingested_content(
        self,
        source_url: str = "",
        source_type: str = "unknown",
        title: str = "",
        word_count: int = 0,
        platform: str = "",
        summary: str = "",
        **kwargs,
    ) -> dict:
        """
        FIX 2: Returns explicit {success, record_id} or {success:False, error}.
        """
        record_id = f"ledger_{uuid.uuid4().hex[:12]}"
        meta = {
            "source_url":  source_url,
            "source_type": source_type,
            "title":       title,
            "word_count":  word_count,
            "platform":    platform,
            "ingested_at": _now(),
        }
        col = _col(COL_CONTENT_LEDGER)
        col.add(ids=[record_id], documents=[summary or title], metadatas=[meta])
        logger.info("Content Ledger: wrote record %s (%s)", record_id, title)
        return {"success": True, "record_id": record_id, "metadata": meta}

    # ── VoiceProfile ─────────────────────────────────────────────────────────
    def get_voice_profile(self) -> dict:
        """
        FIX 3: Returns NOT_FOUND sentinel instead of None.
        content_generator checks for this and aborts rather than hallucinating.
        """
        col = _col(COL_VOICE_PROFILE)
        results = col.get(ids=["current_profile"], include=["documents", "metadatas"])
        if not results["ids"]:
            return NOT_FOUND
        profile_json = results["documents"][0]
        meta = results["metadatas"][0]
        try:
            profile = json.loads(profile_json)
        except json.JSONDecodeError:
            profile = {"raw": profile_json}
        return {
            "status": "OK",
            "profile": profile,
            "version": meta.get("version", 1),
            "updated_at": meta.get("updated_at", "unknown"),
        }

    def upsert_voice_profile(self, voice_signature: dict, **kwargs) -> dict:
        col = _col(COL_VOICE_PROFILE)
        existing = self.get_voice_profile()
        if existing == NOT_FOUND:
            version = 1
            merged = voice_signature
        else:
            version = existing.get("version", 1) + 1
            merged = _deep_merge(existing["profile"], voice_signature)

        # Snapshot the previous version before overwriting.
        if existing != NOT_FOUND:
            snap_id = f"voice_snapshot_v{version - 1}_{uuid.uuid4().hex[:8]}"
            col.add(
                ids=[snap_id],
                documents=[json.dumps(existing["profile"])],
                metadatas={
                    "type": "snapshot",
                    "version": version - 1,
                    "snapped_at": _now(),
                },
            )

        meta = {"version": version, "updated_at": _now()}
        col.upsert(
            ids=["current_profile"],
            documents=[json.dumps(merged)],
            metadatas=[meta],
        )
        logger.info("VoiceProfile upserted — version %d", version)
        return {"success": True, "version": version, "updated_at": meta["updated_at"]}

    # ── Knowledge Graph ───────────────────────────────────────────────────────
    def query_knowledge_graph(self, topic: str, top_k: int = 5) -> dict:
        col = _col(COL_KNOWLEDGE_GRAPH)
        count = col.count()
        if count == 0:
            # FIX 3: Return empty list explicitly so content_generator
            # surfaces the warning rather than generating silently.
            return {"status": "OK", "entries": [], "count": 0,
                    "warning": "Knowledge Graph is empty. Run web_resources_modeling first."}
        results = col.query(
            query_texts=[topic],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )
        entries = [
            {
                "id":        rid,
                "summary":   doc,
                "metadata":  meta,
                "relevance": round(1 - dist, 4),   # cosine similarity proxy
            }
            for rid, doc, meta, dist in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]
        return {"status": "OK", "entries": entries, "count": len(entries)}

    def add_knowledge_entry(
        self,
        summary: str,
        source_url: str = "",
        source_title: str = "",
        relevance_score: float = 0.0,
        credibility_score: float = 0.0,
        key_claims: list[str] | None = None,
        contradicts_author: bool = False,
        **kwargs,
    ) -> dict:
        """FIX 2: Returns explicit record_id or error."""
        record_id = f"kg_{uuid.uuid4().hex[:12]}"
        meta = {
            "source_url":        source_url,
            "source_title":      source_title,
            "relevance_score":   relevance_score,
            "credibility_score": credibility_score,
            "key_claims":        json.dumps(key_claims or []),
            "contradicts_author":str(contradicts_author),
            "added_at":          _now(),
        }
        col = _col(COL_KNOWLEDGE_GRAPH)
        col.add(ids=[record_id], documents=[summary], metadatas=[meta])
        logger.info("KG: wrote entry %s (%s)", record_id, source_title)
        return {"success": True, "record_id": record_id}

    # ── Session Log ───────────────────────────────────────────────────────────
    def log_session_event(
        self,
        event_type: str = "generation",
        topic: str = "",
        format: str = "",
        composite_score: float = 0.0,
        draft_length: int = 0,
        **kwargs,
    ) -> dict:
        record_id = f"session_{uuid.uuid4().hex[:12]}"
        meta = {
            "event_type":      event_type,
            "topic":           topic,
            "format":          format,
            "composite_score": composite_score,
            "draft_length":    draft_length,
            "logged_at":       _now(),
        }
        col = _col(COL_SESSION_LOG)
        col.add(ids=[record_id], documents=[topic], metadatas=[meta])
        logger.info("Session Log: wrote event %s (%s)", record_id, event_type)
        return {"success": True, "record_id": record_id}


    def invoke(self, args: dict, sly_data: dict) -> dict:
        """NeuroSAN CodedTool interface — bridges to run()."""
        operation = args.get("operation", "")
        kwargs = {k: v for k, v in args.items() if k != "operation"}
        return self.run(operation, **kwargs)

    async def async_invoke(self, args: dict, sly_data: dict) -> dict:
        """NeuroSAN async CodedTool interface."""
        return self.invoke(args, sly_data)

# ── helpers ───────────────────────────────────────────────────────────────────

def _deep_merge(base: dict, update: dict) -> dict:
    """
    Merge voice signature dicts.  List fields (top_words, signature_phrases)
    are unioned and de-duplicated; scalar tonal scores are averaged.
    """
    merged = dict(base)
    for k, v in update.items():
        if k not in merged:
            merged[k] = v
        elif isinstance(v, list) and isinstance(merged[k], list):
            # De-duplicate while preserving order.
            seen = set()
            combined = []
            for item in merged[k] + v:
                key = item if isinstance(item, str) else json.dumps(item, sort_keys=True)
                if key not in seen:
                    seen.add(key)
                    combined.append(item)
            merged[k] = combined
        elif isinstance(v, (int, float)) and isinstance(merged[k], (int, float)):
            # Average numeric scores (tonal dimensions etc.)
            merged[k] = round((merged[k] + v) / 2, 2)
        else:
            merged[k] = v   # update wins for strings / nested dicts
    return merged