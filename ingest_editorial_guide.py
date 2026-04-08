#!/usr/bin/env python3
import os, io, json, sys, requests
from pypdf import PdfReader

PDF_URL = "https://arxiv.org/pdf/2603.18161"
CHUNK_CACHE_PATH = "editorial_guide__chunks.json"
GUIDE_CACHE_PATH = "editorial_guide__anti_ai_slop.txt"

ROLE_HEADER = "\n".join([
    "ROLE: EDITORIAL DIRECTIVE - WRITING STANDARDS",
    "SOURCE: How LLMs Distort Our Written Language - Abdulhai, White et al., 2026",
    "THIS IS NOT A KNOWLEDGE SOURCE.",
    "APPLY TO: All written output, post-research, pre-delivery.",
    "BLOCK: Filler affirmations, hedge stacking, neutral stance drift,",
    "pronoun erasure, emotional inflation, analytical inflation,",
    "colloquialism removal, vocabulary substitution, conclusion-altering edits.",
    "PRESERVE: Argumentative stance, first-person voice, anecdotes,",
    "author lexical fingerprint, original conclusions.",
    "=" * 72,
    ""
])

if os.path.exists(CHUNK_CACHE_PATH) and os.path.exists(GUIDE_CACHE_PATH):
    with open(CHUNK_CACHE_PATH) as f:
        existing = json.load(f)
    print("Already ingested (" + str(len(existing)) + " pages).")
    sys.exit(0)

print("Fetching PDF from arXiv...")
r = requests.get(PDF_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
r.raise_for_status()
print("Downloaded (" + str(len(r.content)//1024) + " KB)")

reader = PdfReader(io.BytesIO(r.content))
chunks = []
total = len(reader.pages)
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if text and text.strip():
        chunks.append({"page": i+1, "text": text.strip()})
    if (i+1) % 10 == 0 or (i+1) == total:
        print(str(i+1) + "/" + str(total) + " pages...", end="\r")

print("\n" + str(len(chunks)) + " pages extracted")

full = ROLE_HEADER
for c in chunks:
    full += "\n\n--- Page " + str(c["page"]) + " ---\n" + c["text"]

with open(CHUNK_CACHE_PATH, "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)
with open(GUIDE_CACHE_PATH, "w", encoding="utf-8") as f:
    f.write(full)

print("Saved: " + CHUNK_CACHE_PATH)
print("Saved: " + GUIDE_CACHE_PATH)
print("Done. Editorial directive is active.")
