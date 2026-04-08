import json, os, time
import chromadb
from chromadb.config import Settings

_CHROMA_PATH = os.environ.get("RAVI_CHROMA_PATH", "./ravi_chroma_db")

def _col(name):
    return chromadb.PersistentClient(
        path=_CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False)
    ).get_or_create_collection(name)

class MemoryStoreTool:
    def invoke(self, args: dict, sly_data: dict = None) -> dict:
        try:
            collection = args.get("collection")
            content    = args.get("content")
            if not collection or not content:
                return {"error": "Missing required args: collection, content"}
            metadata = args.get("metadata") or {}
            doc_id   = args.get("id") or f"{collection}_{int(time.time()*1000)}"
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            metadata["timestamp"] = ts
            _col(collection).upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[{k: str(v) for k, v in metadata.items()}]
            )
            return {"status": "ok", "id": doc_id, "collection": collection, "timestamp": ts}
        except Exception as e:
            return {"error": str(e)}
