"""
ingest_linkedin_posts.py
Ingest Ravi Kumar S LinkedIn posts (2025-2026) into ChromaDB ravi_voice_knowledge.
Run from /workspaces/neuro-san-studio with venv active.
Requires: pip install python-docx chromadb
"""

import re
import sys
import chromadb

CHROMA_PATH = "./ravi_chroma_db"
COLLECTION  = "ravi_voice_knowledge"
DOCX_PATH   = "./ravi_linkedin_posts.txt"  # pre-extracted text file

HEADER_RE = re.compile(
    r'.*(?:original post|amplify .+? post).*\d',
    re.IGNORECASE
)


def parse_posts(text):
    posts = []
    current_title = None
    current_type  = "original"
    current_lines = []

    for line in text.split("\n"):
        stripped = line.strip()
        if HEADER_RE.match(stripped) and len(stripped) < 250:
            if current_title and current_lines:
                body = "\n".join(current_lines).strip()
                if len(body) > 20:
                    posts.append((current_title, current_type, body))
            m = re.match(
                r"^(.+?)(?:\.\s*(?:Original post|amplify)|\s*\(amplify)",
                stripped, re.IGNORECASE
            )
            current_title = m.group(1).strip() if m else stripped[:80]
            current_type  = "amplification" if "amplify" in stripped.lower() else "original"
            current_lines = []
        else:
            current_lines.append(line)

    if current_title and current_lines:
        body = "\n".join(current_lines).strip()
        if len(body) > 20:
            posts.append((current_title, current_type, body))

    return posts


def ingest():
    # Extract text from docx if needed
    try:
        from docx import Document
        doc = Document("./RKS_LinkedIn_2025-2026.docx")
        text = "\n".join([p.text for p in doc.paragraphs])
        print(f"Extracted {len(text)} chars from docx")
    except Exception as e:
        print(f"docx read failed ({e}), trying txt fallback...")
        text = open(DOCX_PATH).read()

    posts = parse_posts(text)
    originals = sum(1 for p in posts if p[1] == "original")
    print(f"Parsed {len(posts)} posts ({originals} original, {len(posts)-originals} amplification)")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    col    = client.get_or_create_collection(COLLECTION)

    added = skipped = 0
    for i, (title, ptype, body) in enumerate(posts):
        doc_id = f"ravi_linkedin_{i:03d}"

        existing = col.get(ids=[doc_id])
        if existing["ids"]:
            skipped += 1
            continue

        # Only ingest substantive content (skip very short amplifications)
        if len(body) < 50:
            skipped += 1
            continue

        doc_text = (
            f"Ravi Kumar S LinkedIn post — {title}\n"
            f"Type: {'Original authored post' if ptype == 'original' else 'Amplification/share'}\n\n"
            f"{body}"
        )

        col.add(
            ids=[doc_id],
            documents=[doc_text],
            metadatas=[{
                "source":     "RKS_LinkedIn_2025_2026",
                "type":       "linkedin_post_verbatim",
                "post_type":  ptype,
                "title":      title,
                "voice":      "verbatim_ravi_kumar_s",
                "collection": COLLECTION,
                "topic":      "linkedin_voice_style_corpus",
                "date":       "2025-2026",
            }]
        )
        added += 1
        if added % 20 == 0:
            print(f"  Ingested {added} posts...")

    print(f"\nDone. Added: {added}, Skipped: {skipped}")
    print(f"Collection total: {col.count()} documents")


if __name__ == "__main__":
    ingest()
