from neuro_san.interfaces.coded_tool import CodedTool
import json, logging, os, uuid
from datetime import datetime, timezone
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)
_CHROMA_PATH = os.environ.get("RAVI_CHROMA_PATH", "./ravi_chroma_db")

ALL_COLLECTIONS = [
    "ravi_voice_knowledge",
    "content_ledger",
    "voice_profile",
    "knowledge_graph",
    "session_log",
]

_client = None

def _get_client():
    global _client
    if _client is not None:
        return _client
    _client = chromadb.PersistentClient(
        path=_CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    logger.info("MemoryStoreTool: PersistentClient at %s", _CHROMA_PATH)
    return _client

def _col(name):
    return _get_client().get_or_create_collection(name=name)

def _now():
    return datetime.now(timezone.utc).isoformat()

def _sanitize_metadata(meta: dict) -> dict:
    safe = {}
    for k, v in meta.items():
        if v is None:
            continue
        safe[k] = v if isinstance(v, (str, int, float, bool)) else json.dumps(v)
    return safe


def _unwrap(args: dict) -> dict:
    """NeuroSAN wraps payload inside tool_args.args[0] or tool_args flat dict."""
    if not isinstance(args, dict) or "tool_args" not in args:
        return args
    ta = args["tool_args"]
    if not isinstance(ta, dict):
        return args
    inner = ta.get("args", [])
    if isinstance(inner, list) and inner and isinstance(inner[0], dict):
        return inner[0]
    # flat form: collection/content at top level of tool_args
    return {k: v for k, v in ta.items() if k not in ("args", "origin")}

class MemoryStoreTool(CodedTool):
    def invoke(self, args: dict, sly_data: dict = None) -> dict:
        # NeuroSAN passes args as tool_args.args[0] (list) or tool_args (dict)
        if "tool_args" in args:
            ta = args["tool_args"]
            if isinstance(ta, dict):
                inner = ta.get("args", [])
                if isinstance(inner, list) and inner:
                    args = inner[0]   # args[0] is the actual payload dict
                else:
                    # flat tool_args: collection/content at top level
                    args = {k: v for k, v in ta.items()
                            if k not in ("args", "origin")}
        op = args.get("operation", "store")
        fn = {
            "store":                 self._store,
            "store_knowledge":       self._store_knowledge,
            "health_check":          self._health_check,
            "bootstrap_collections": self._bootstrap,
        }.get(op, self._store)
        kwargs = {k: v for k, v in args.items() if k != "operation"}
        try:
            return fn(**kwargs)
        except Exception as exc:
            logger.exception("MemoryStoreTool error in '%s'", op)
            return {"success": False, "error": str(exc)}

    def _store(self, collection=None, content=None, text=None, summary=None,
               document=None, data=None, metadata=None, id=None, **kwargs):
        collection = collection or "ravi_voice_knowledge"
        # Aggressively extract content from any argument the agent passes
        content = (content or text or summary or document or
                   (json.dumps(data) if data else None))
        # Last resort: pull from any remaining kwargs that look like content
        SKIP_KEYS = {"origin", "origin_str", "tool", "instantiation_index"}
        if not content or str(content).strip() in ("", "{}"):
            for k, v in kwargs.items():
                if k not in SKIP_KEYS and isinstance(v, str) and len(v) > 20:
                    content = v
                    logger.info("_store: extracted content from kwarg '%s'", k)
                    break
        if not content or str(content).strip() in ("", "{}"):
            # Log the full args for debugging before failing
            logger.error(
                "_store called with no usable content. "
                "collection=%s kwargs_keys=%s", collection, list(kwargs.keys())
            )
            return {"success": False, "error": "No content provided",
                    "hint": "Pass content= or text= or summary= with the text to store"}
        record_id = id or f"mem_{uuid.uuid4().hex[:16]}"
        meta = _sanitize_metadata(metadata if isinstance(metadata, dict)
                                  else (json.loads(metadata)
                                        if isinstance(metadata, str) and metadata
                                        else {}))
        meta.setdefault("stored_at", _now())
        meta.setdefault("collection", collection)
        _col(collection).add(
            ids=[record_id],
            documents=[str(content)],
            metadatas=[meta],
        )
        logger.info("store: %s → %s", record_id, collection)
        return {"success": True, "record_id": record_id, "collection": collection}

    def _store_knowledge(self, summary="", source_url="",
                         source_title="", topic="", **kwargs):
        meta = {"source_url": source_url, "source_title": source_title,
                "topic": topic, "added_at": _now()}
        result = self._store(collection="ravi_voice_knowledge",
                             content=summary, metadata=meta)
        if result.get("success"):
            kg_id = f"kg_{uuid.uuid4().hex[:12]}"
            _col("knowledge_graph").add(
                ids=[kg_id], documents=[summary],
                metadatas=[_sanitize_metadata(meta)])
            result["kg_record_id"] = kg_id
        return result

    def _health_check(self, **kwargs):
        try:
            client = _get_client()
            cols = [c.name for c in client.list_collections()]
            return {"status": "OK", "collections": cols,
                    "missing": [c for c in ALL_COLLECTIONS if c not in cols],
                    "path": _CHROMA_PATH, "timestamp": _now()}
        except Exception as exc:
            return {"status": "ERROR", "error": str(exc), "timestamp": _now()}

    def _bootstrap(self, **kwargs):
        created, existing = [], []
        for name in ALL_COLLECTIONS:
            col = _col(name)
            (existing if col.count() > 0 else created).append(name)
        logger.info("bootstrap: created=%s existing=%s", created, existing)
        return {"success": True, "created": created, "existing": existing}
