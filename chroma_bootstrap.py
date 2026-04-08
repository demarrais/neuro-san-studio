"""
chroma_bootstrap.py
-------------------
Run this ONCE before starting the rAvI agent network.
It connects to the running ChromaDB instance and initializes
all four required collections if they don't already exist.

Usage:
    python chroma_bootstrap.py

Requirements:
    - ChromaDB must already be running: chroma run --path ./chroma_db
    - pip install chromadb
"""

import chromadb
from chromadb.config import Settings

# ── Config ────────────────────────────────────────────────
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

# The four rAvI collections
COLLECTIONS = [
    {
        "name": "ravi_voice_knowledge",
        "description": "Semantic knowledge base for ravi voice style and ingested content",
        "metadata": {"hnsw:space": "cosine"},
        "metadata": {"hnsw:space": "cosine"}
    },
    {
        "name": "ravi_voice_knowledge",
        "description": "Semantic knowledge base for ravi voice style and ingested content",
        "metadata": {"hnsw:space": "cosine"},
        "metadata": {"hnsw:space": "cosine"}
    },
    {
        "name": "content_ledger",
        "description": "Index of all ingested items with metadata (URLs, local files, social posts)"
    },
    {
        "name": "voice_profile",
        "description": "Versioned author voice model — updated after each analysis"
    },
    {
        "name": "knowledge_graph",
        "description": "Researched facts and sources with provenance and relevance scores"
    },
    {
        "name": "session_log",
        "description": "Full history of all generation events and voice authenticity scores"
    }
]

# ── Bootstrap ─────────────────────────────────────────────
def bootstrap():
    print(f"\n🔗 Connecting to ChromaDB at http://{CHROMA_HOST}:{CHROMA_PORT} ...\n")

    try:
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=Settings(anonymized_telemetry=False)
        )
        # Verify connection
        client.heartbeat()
        print("✅ Connected to ChromaDB\n")
    except Exception as e:
        print(f"❌ Could not connect to ChromaDB: {e}")
        print("   Make sure ChromaDB is running: chroma run --path ./chroma_db\n")
        return

    for col in COLLECTIONS:
        try:
            existing = client.get_collection(name=col["name"])
            print(f"⏭️  '{col['name']}' already exists — skipping (count: {existing.count()})")
        except Exception:
            # Collection doesn't exist — create it
            client.create_collection(
                name=col["name"],
                metadata={"description": col["description"]}
            )
            print(f"✅ Created collection: '{col['name']}'")

    print("\n─────────────────────────────────────────")
    print("✅ Bootstrap complete. All collections ready.")
    print("   You can now start the rAvI agent network.\n")


if __name__ == "__main__":
    bootstrap()
