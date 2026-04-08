from neuro_san.interfaces.coded_tool import CodedTool
import json, logging, os, uuid
from datetime import datetime, timezone
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)
_CHROMA_PATH = os.environ.get("RAVI_CHROMA_PATH", "./ravi_chroma_db")
NOT_FOUND = {"status": "NOT_FOUND"}

_client = None

def _get_client():
    global _client
    if _client is not None:
        return _client
    _client = chromadb.PersistentClient(
        path=_CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    logger.info("MemoryQueryTool: PersistentClient at %s", _CHROMA_PATH)
    return _client

def _col(name):
    return _get_client().get_or_create_collection(name=name)

def _now():
    return datetime.now(timezone.utc).isoformat()


class MemoryQueryTool(CodedTool):
    # VERSION MARKER — forces server reload
    _VERSION = "v3-1774618246"

    def invoke(self, args: dict, sly_data: dict = None) -> dict:
        # v1774628877 — handles all 4 NeuroSAN payload forms including progress_reporter
        # Form D (NEW): {"args": {...}, "origin": [...], "origin_str": "...", "progress_reporter": ...}
        # Form A: {"tool_args": {"args": [{...}], ...}}
        # Form B: {"tool_args": {"args": {...}, ...}}
        # Form C: {"tool_args": {flat}, ...}
        ta = args.get("tool_args")
        if isinstance(ta, dict):
            inner = ta.get("args")
            if isinstance(inner, list) and inner and isinstance(inner[0], dict):
                args = inner[0]
            elif isinstance(inner, dict) and inner:
                args = inner
            else:
                stripped = {k: v for k, v in ta.items()
                            if k not in ("args","origin","origin_str","tool_start","progress_reporter")}
                if stripped:
                    args = stripped
        elif "args" in args and isinstance(args.get("args"), dict):
            # Form D: flat dict with nested "args" key
            args = args["args"]
        if "query" in args and "operation" not in args:
            return self._query(
                args.get("query",""),
                args.get("collection","ravi_voice_knowledge"),
                args.get("top_k",5)
            )
        op = args.get("operation","query")
        fn = {"health_check":self._health_check,
               "query":self._query_from_args,"search":self._query_from_args,
               "query_voice_knowledge":self._query_from_args,
               "get_content_ledger":self._get_content_ledger,
               "get_voice_profile":self._get_voice_profile,
               "upsert_voice_profile":self._upsert_voice_profile,
               "query_knowledge_graph":self._query_knowledge_graph,
               "add_knowledge_entry":self._add_knowledge_entry,
               "log_session_event":self._log_session_event,
               "log_ingested_content":self._log_ingested_content}.get(op)
        if fn is None:
            return {"success":False,"error":f"Unknown operation: {op}"}
        try:
            return fn(**{k:v for k,v in args.items() if k!="operation"})
        except Exception as exc:
            return {"success":False,"error":str(exc)}

    async def async_invoke(self, args: dict, sly_data: dict = None) -> dict:
        return self.invoke(args, sly_data)


    def _query_from_args(self, **kwargs):
        return self._query(
            query=kwargs.get("query", ""),
            collection=kwargs.get("collection", "ravi_voice_knowledge"),
            top_k=kwargs.get("top_k", 5),
        )

    def _query(self, query="", collection="ravi_voice_knowledge", top_k=5):
        if not query:
            return {"status": "ERROR", "error": "query is required"}
        col = _col(collection)
        count = col.count()
        if count == 0:
            return {"status": "EMPTY", "documents": [], "count": 0,
                    "warning": f"Collection '{collection}' is empty. Ingest content first."}
        results = col.query(
            query_texts=[query],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )
        documents = [
            {"id": rid, "content": doc, "metadata": meta,
             "relevance": round(1 - dist, 4)}
            for rid, doc, meta, dist in zip(
                results["ids"][0], results["documents"][0],
                results["metadatas"][0], results["distances"][0],
            )
        ]
        logger.info("query: collection='%s' hits=%d", collection, len(documents))
        return {"status": "OK", "documents": documents,
                "count": len(documents), "collection": collection}

    def _health_check(self, **_):
        try:
            client = _get_client()
            cols = [c.name for c in client.list_collections()]
            return {"status": "OK", "collections": cols,
                    "path": _CHROMA_PATH, "timestamp": _now()}
        except Exception as exc:
            return {"status": "ERROR", "error": str(exc), "timestamp": _now()}

    def _get_content_ledger(self, **_):
        col = _col("content_ledger")
        results = col.get(include=["metadatas", "documents"])
        if not results["ids"]:
            return {"status": "OK", "records": [], "count": 0}
        return {"status": "OK", "count": len(results["ids"]),
                "records": [{"id": i, "metadata": m, "summary": d}
                            for i, m, d in zip(results["ids"],
                                               results["metadatas"],
                                               results["documents"])]}

    def _get_voice_profile(self, **_):
        col = _col("voice_profile")
        results = col.get(ids=["current_profile"],
                          include=["documents", "metadatas"])
        if not results["ids"]:
            return NOT_FOUND
        try:
            profile = json.loads(results["documents"][0])
        except json.JSONDecodeError:
            profile = {"raw": results["documents"][0]}
        meta = results["metadatas"][0]
        return {"status": "OK", "profile": profile,
                "version": meta.get("version", 1),
                "updated_at": meta.get("updated_at", "unknown")}

    def _upsert_voice_profile(self, voice_signature: dict = None, **kwargs):
        if not voice_signature:
            return {"success": False, "error": "voice_signature is required"}
        col = _col("voice_profile")
        existing = self._get_voice_profile()
        version = 1 if existing == NOT_FOUND else existing.get("version", 1) + 1
        merged = voice_signature if existing == NOT_FOUND else \
            _deep_merge(existing["profile"], voice_signature)
        col.upsert(ids=["current_profile"],
                   documents=[json.dumps(merged)],
                   metadatas=[{"version": version, "updated_at": _now()}])
        return {"success": True, "version": version, "updated_at": _now()}

    def _query_knowledge_graph(self, topic="", top_k=5, **kwargs):
        return self._query(query=topic, collection="knowledge_graph", top_k=top_k)

    def _add_knowledge_entry(self, summary="", source_url="", source_title="",
                              relevance_score=0.0, credibility_score=0.0,
                              key_claims=None, contradicts_author=False, **kwargs):
        record_id = f"kg_{uuid.uuid4().hex[:12]}"
        meta = {"source_url": source_url, "source_title": source_title,
                "relevance_score": relevance_score,
                "credibility_score": credibility_score,
                "key_claims": json.dumps(key_claims or []),
                "contradicts_author": str(contradicts_author),
                "added_at": _now()}
        _col("knowledge_graph").add(ids=[record_id],
                                    documents=[summary], metadatas=[meta])
        return {"success": True, "record_id": record_id}

    def _log_session_event(self, event_type="generation", topic="",
                            format="", composite_score=0.0,
                            draft_length=0, **kwargs):
        record_id = f"session_{uuid.uuid4().hex[:12]}"
        _col("session_log").add(
            ids=[record_id], documents=[topic],
            metadatas=[{"event_type": event_type, "topic": topic,
                        "format": format, "composite_score": composite_score,
                        "draft_length": draft_length, "logged_at": _now()}])
        return {"success": True, "record_id": record_id}

    def _log_ingested_content(self, source_url="", source_type="unknown",
                               title="", word_count=0, platform="",
                               summary="", **kwargs):
        record_id = f"ledger_{uuid.uuid4().hex[:12]}"
        meta = {"source_url": source_url, "source_type": source_type,
                "title": title, "word_count": word_count,
                "platform": platform, "ingested_at": _now()}
        _col("content_ledger").add(ids=[record_id],
                                   documents=[summary or title],
                                   metadatas=[meta])
        return {"success": True, "record_id": record_id}

def _deep_merge(base: dict, update: dict) -> dict:
    merged = dict(base)
    for k, v in update.items():
        if k not in merged:
            merged[k] = v
        elif isinstance(v, list) and isinstance(merged[k], list):
            seen, combined = set(), []
            for item in merged[k] + v:
                key = item if isinstance(item, str) else json.dumps(item, sort_keys=True)
                if key not in seen:
                    seen.add(key)
                    combined.append(item)
            merged[k] = combined
        elif isinstance(v, (int, float)) and isinstance(merged[k], (int, float)):
            merged[k] = round((merged[k] + v) / 2, 2)
        else:
            merged[k] = v
    return merged
