from neuro_san.interfaces.coded_tool import CodedTool
import os, uuid
import chromadb

_CHROMA_PATH = os.environ.get("RAVI_CHROMA_PATH", "./ravi_chroma_db")

def _client():
    return chromadb.PersistentClient(path=_CHROMA_PATH)

def _col(name):
    return _client().get_or_create_collection(name)

class MemoryQueryTool(CodedTool):
    def invoke(self, args: dict, sly_data: dict = None) -> dict:
        try:
            if args.get("list_collections"):
                return {"status": "ok", "collections": [c.name for c in _client().list_collections()]}
            if args.get("operation") == "add_entry" or args.get("add_entry"):
                collection = args.get("collection", "knowledge_graph")
                document = args.get("document") or args.get("summary") or args.get("content", "")
                metadata = {k: args[k] for k in ("topic", "source_title") if k in args}
                record_id = args.get("id") or f"kg_{uuid.uuid4().hex[:12]}"
                _col(collection).upsert(ids=[record_id], documents=[document], metadatas=[metadata])
                return {"status": "ok", "record_id": record_id}
            collection = args.get("collection")
            if not collection:
                return {"error": "Missing collection"}
            col = _col(collection)
            count = col.count()
            if count == 0:
                return {"status": "empty", "results": []}
            query_text = args.get("query") or args.get("inquiry")
            if not query_text:
                return {"error": "Provide query or add_entry"}
            n = min(int(args.get("n_results", 5)), count)
            r = col.query(query_texts=[query_text], n_results=n, include=["documents","metadatas","distances"])
            return {"status": "ok", "results": [{"document": d, "metadata": m, "distance": x} for d,m,x in zip(r["documents"][0],r["metadatas"][0],r["distances"][0])]}
        except Exception as e:
            return {"error": str(e)}

    async def async_invoke(self, args: dict, sly_data: dict = None) -> dict:
        return self.invoke(args, sly_data)
