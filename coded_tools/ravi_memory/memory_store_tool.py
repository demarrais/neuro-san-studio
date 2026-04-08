from neuro_san.interfaces.coded_tool import CodedTool
import os, time
import chromadb

_CHROMA_PATH = os.environ.get("RAVI_CHROMA_PATH", "./ravi_chroma_db")

def _col(name):
    return chromadb.PersistentClient(path=_CHROMA_PATH).get_or_create_collection(name)

class MemoryStoreTool(CodedTool):
    def invoke(self, args: dict, sly_data: dict = None) -> dict:
        try:
            collection = args.get("collection") or "ravi_voice_knowledge"
            text = (args.get("content") or args.get("text") or
                    args.get("summary") or args.get("document") or
                    args.get("data") or str(args))
            if not text or text == "{}":
                return {"error": "No content provided"}
            metadata = args.get("metadata") or {}
            if isinstance(metadata, str):
                metadata = {"info": metadata}
            doc_id = args.get("id") or f"{collection}_{int(time.time()*1000)}"
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            metadata["timestamp"] = ts
            _col(collection).upsert(
                ids=[doc_id],
                documents=[text],
                metadatas=[{k: str(v) for k, v in metadata.items()}]
            )
            return {"status": "ok", "id": doc_id, "collection": collection, "timestamp": ts}
        except Exception as e:
            return {"error": str(e)}

    async def async_invoke(self, args, sly_data):
        return self.invoke(args, sly_data)
