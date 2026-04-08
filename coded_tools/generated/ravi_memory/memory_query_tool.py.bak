import json, os, time
import chromadb
from chromadb.config import Settings

_CHROMA_PATH = os.environ.get("RAVI_CHROMA_PATH", "./ravi_chroma_db")

def _client():
    return chromadb.PersistentClient(
        path=_CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False)
    )

def _col(name):
    return _client().get_or_create_collection(name)

class MemoryQueryTool:
    def invoke(self, args: dict, sly_data: dict = None) -> dict:
        try:
            # list_collections mode
            if args.get("list_collections"):
                cols = [c.name for c in _client().list_collections()]
                return {"status": "ok", "collections": cols}

            collection = args.get("collection")
            if not collection:
                return {"error": "Missing required arg: collection"}

            col = _col(collection)
            count = col.count()
            if count == 0:
                return {"status": "empty", "results": []}

            # fetch by ID
            doc_id = args.get("id")
            if doc_id:
                r = col.get(ids=[doc_id], include=["documents", "metadatas"])
                if not r["ids"]:
                    return {"status": "not_found", "id": doc_id}
                return {"status": "ok", "id": r["ids"][0],
                        "document": r["documents"][0],
                        "metadata": r["metadatas"][0]}

            # semantic search
            query_text = args.get("query") or args.get("inquiry")
            if not query_text:
                return {"error": "Provide either query or id"}

            n = min(int(args.get("n_results", 5)), count)
            r = col.query(
                query_texts=[query_text],
                n_results=n,
                include=["documents", "metadatas", "distances"]
            )
            results = [
                {"document": doc, "metadata": meta, "distance": dist}
                for doc, meta, dist in zip(
                    r["documents"][0], r["metadatas"][0], r["distances"][0]
                )
            ]
            return {"status": "ok", "collection": collection,
                    "count": len(results), "results": results}
        except Exception as e:
            return {"error": str(e)}
