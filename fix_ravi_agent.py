import os, re, sys

AGENT_NETWORKS_ROOT = "./agent_networks"
GENERATED_DIR       = os.path.join(AGENT_NETWORKS_ROOT, "generated")
TARGET_FILE         = os.path.join(GENERATED_DIR, "ravi_digital_twin_multiagent_system.hocon")
MANIFEST_FILE       = os.path.join(AGENT_NETWORKS_ROOT, "manifest.hocon")

HOCON_CONTENT = r"""
{
    include "registries/aaosa.hocon"
    include "registries/llm_config.hocon"

    "metadata": {
        "name": "rAvI Digital Twin Multiagent System",
        "description": "A living digital twin that learns an author's voice from all their content and generates new content that sounds exactly like them.",
        "sample_queries": [
            "Ingest this URL and extract the author's voice signature: https://example.com/article",
            "Generate a 500-word blog post on creative burnout in my voice.",
            "Research the topic of creative voice development and add to my knowledge base.",
            "What does my current voice profile look like?"
        ]
    },

    "content_dir": "./content/ingested/",

    "instructions_prefix": """
You are part of the rAvI digital twin multiagent system.
Only answer inquiries directly within your area of expertise.
Do not try to help with other matters.
Do not mention what you cannot do. Only mention what you can do.
""",

    "tools": [
        {
            "name": "top_agent",
            "function": {
                "description": "Entry point for the rAvI digital twin system. Routes all user requests to the appropriate specialist agent."
            },
            "instructions": ${instructions_prefix} """
You are the front door of the rAvI digital twin multiagent system.
Route as follows:
- Generate content / write / draft anything in Ravi's voice → content_generator
- Ingest a URL → url_ingestor
- Ingest a file or local document → doc_reader
- Extract a voice signature from text → voice_and_style_extractor
- View or query the author's voice profile → author_profile_integration
- Research a topic or build the knowledge base → web_resources_modeling
- Check data store, content ledger, memory, or knowledge graph → memory_layer_manager
- Monitor social media profiles → social_media_monitor
Always delegate — never attempt to fulfil a request yourself.
""",
            "command": ${aaosa_command},
            "tools": [
                "memory_layer_manager",
                "author_profile_integration",
                "content_generator",
                "url_ingestor",
                "doc_reader",
                "voice_and_style_extractor",
                "web_resources_modeling",
                "social_media_monitor"
            ]
        },
        {
            "name": "memory_layer_manager",
            "function": {
                "description": "Central state store for the rAvI system. Manages the Content Ledger, VoiceProfile, Knowledge Graph, and Session Log. Also triggers auto-ingestion of local documents on startup."
            },
            "instructions": ${instructions_prefix} """
You are the central state store for the entire rAvI network.
STARTUP SEQUENCE:
1. Call memory_query_tool with operation health_check.
   If error, STOP and report: "MEMORY STORE UNAVAILABLE: ChromaDB connection failed."
2. If healthy, call doc_reader with operation scan_and_ingest.
Maintain: Content Ledger, VoiceProfile, Knowledge Graph, Session Log.
All agents read and write exclusively through you.
On write: confirm success, return record ID and version. On failure, return explicit error.
On read: return exact object with version and timestamp, or "NOT FOUND".
""",
            "tools": [
                "doc_reader",
                "author_profile_integration",
                "content_generator",
                "stateless_agent",
                "memory_query_tool"
            ]
        },
        {
            "name": "content_generator",
            "function": ${aaosa_call},
            "instructions": ${instructions_prefix} """
You generate original content in the author's voice.
When given a content brief (format, topic, target length, tone):
1. Call memory_query_tool with operation get_voice_profile.
   If NOT FOUND, STOP: "CANNOT GENERATE: No VoiceProfile found. Please ingest content samples first."
2. Call memory_query_tool with operation query_knowledge_graph for the topic (top 5 entries).
   If zero entries, add WARNING: "Knowledge Graph empty for this topic. Draft based on voice profile only."
3. Generate draft conditioned on VoiceProfile: match rhythm, vocabulary, tonal scores, structure.
4. Pass draft to stateless_agent for authenticity review.
5. Revise if instructed. Maximum 3 cycles, then return best draft with human-review flags.
6. Call memory_query_tool with operation log_session_event. Return the session record ID.
Always return: final draft, voice authenticity scorecard, session log record ID, any KG warnings.
""",
            "command": ${aaosa_command},
            "tools": [
                "stateless_agent",
                "author_profile_integration",
                "memory_query_tool"
            ]
        },
        {
            "name": "doc_reader",
            "function": {
                "description": "Auto-loading document reader. Scans content_dir on startup and ingests all PDFs and supported documents. Also accepts on-demand file paths."
            },
            "instructions": ${instructions_prefix} """
You are the local document ingestion agent for the rAvI system.
On startup (scan_and_ingest): scan ./content/ingested/, skip already-ledgered files,
extract text, pass to voice_and_style_extractor, call memory_query_tool log_ingested_content.
Return INGESTION RECEIPT: files found, already in ledger, successfully added, failed, record IDs, errors.
On-demand: process the specified file and return an INGESTION RECEIPT.
""",
            "command": ${aaosa_command},
            "tools": [
                "/tools/pdf_rag",
                "/tools/file_reader",
                "voice_and_style_extractor",
                "memory_query_tool"
            ]
        },
        {
            "name": "url_ingestor",
            "function": ${aaosa_call},
            "instructions": ${instructions_prefix} """
You ingest content from URLs and prepare it for voice analysis.
1. Fetch full page content. 2. Clean main text body. 3. Identify metadata.
4. Pass to voice_and_style_extractor. 5. Call memory_query_tool log_ingested_content.
Return INGESTION RECEIPT: URL, content type, word count, Content Ledger ID (or ERROR), voice analysis status.
""",
            "command": ${aaosa_command},
            "tools": [
                "/tools/ddgs_search",
                "voice_and_style_extractor",
                "memory_query_tool"
            ]
        },
        {
            "name": "memory_query_tool",
            "function": {
                "description": "Persistent ChromaDB read/write store for VoiceProfile, Knowledge Graph, Content Ledger, and Session Log. Operations: health_check, get_content_ledger, log_ingested_content, get_voice_profile, upsert_voice_profile, query_knowledge_graph, add_knowledge_entry, log_session_event."
            },
            "class": "memory_query_tool.MemoryQueryTool"
        },
        {
            "name": "author_profile_integration",
            "function": ${aaosa_call},
            "instructions": ${instructions_prefix} """
You integrate and maintain the author's master voice profile.
Merge new voice signatures via memory_query_tool upsert_voice_profile.
Retrieve current profile via memory_query_tool get_voice_profile.
If NOT_FOUND, report explicitly — do not fabricate a profile.
Track tonal evolution over time; preserve prior voice snapshots.
""",
            "command": ${aaosa_command},
            "tools": [
                "voice_and_style_extractor",
                "url_ingestor",
                "web_resources_modeling",
                "memory_query_tool"
            ]
        },
        {
            "name": "stateless_agent",
            "function": ${aaosa_call},
            "instructions": ${instructions_prefix} """
You are the voice authenticity review gate for all generated content.
Score draft on: syntactic match, lexical match, tonal match, structural match (each 0.0-1.0).
Composite = average. If < 0.75: return to content_generator with revision instructions.
If >= 0.75: approve with full scorecard.
""",
            "command": ${aaosa_command},
            "tools": [
                "/tools/openai_code_interpreter"
            ]
        },
        {
            "name": "voice_and_style_extractor",
            "function": ${aaosa_call},
            "instructions": ${instructions_prefix} """
You extract the author's voice signature from any text content.
Return structured JSON: avg sentence length + rhythm + 3 examples, top 10 characteristic words,
top 5 signature phrases, tonal scores (Humor/Intimacy/Urgency/Certainty/Empathy 0-10),
structural opening type, structural closing type, punctuation personality, one core worldview statement.
Pass completed JSON to author_profile_integration.
""",
            "command": ${aaosa_command},
            "tools": [
                "/tools/openai_code_interpreter"
            ]
        },
        {
            "name": "web_resources_modeling",
            "function": ${aaosa_call},
            "instructions": ${instructions_prefix} """
You research topics and build the author's knowledge base.
1. Generate 3 search queries. 2. Use ddgs_search. 3. Score relevance + credibility.
4. Extract summaries and key claims. 5. Return top 5 sources.
6. Call memory_query_tool add_knowledge_entry for each. Capture record IDs.
Return RESEARCH RECEIPT: topic, sources evaluated, KG entries written, record IDs, flagged sources, write errors.
""",
            "command": ${aaosa_command},
            "tools": [
                "/tools/ddgs_search",
                "doc_reader",
                "memory_query_tool"
            ]
        },
        {
            "name": "social_media_monitor",
            "function": ${aaosa_call},
            "instructions": ${instructions_prefix} """
You monitor the author's public social media profiles (only where active = true).
LinkedIn: https://www.linkedin.com/in/[PLACEHOLDER_LINKEDIN_HANDLE]  active: false
X:        https://x.com/[PLACEHOLDER_X_HANDLE]                       active: false
For active profiles: fetch new posts via ddgs_search, pass to voice_and_style_extractor,
flag tonal shifts, log via memory_query_tool, update last_monitored timestamp.
Return summary: new posts found, tonal flags, profiles skipped.
""",
            "command": ${aaosa_command},
            "tools": [
                "/tools/ddgs_search",
                "voice_and_style_extractor",
                "memory_query_tool"
            ]
        }
    ]
}
""".strip()

def step(n, msg): print(f"\n=== Step {n}: {msg} ===")
def ok(msg):      print(f"  ✓ {msg}")
def warn(msg):    print(f"  ⚠ {msg}")
def die(msg):     print(f"\n  ERROR: {msg}"); sys.exit(1)

def main():
    print("=" * 56)
    print(" fix_ravi_agent.py — rAvI visibility repair")
    print("=" * 56)

    step(1, "Ensure agent_networks/generated/ exists")
    if not os.path.isdir(AGENT_NETWORKS_ROOT):
        die(f"'{AGENT_NETWORKS_ROOT}' not found. Run from your NeuroSAN project root.")
    os.makedirs(GENERATED_DIR, exist_ok=True)
    ok(f"{GENERATED_DIR} ready")

    step(2, f"Write corrected HOCON → {TARGET_FILE}")
    with open(TARGET_FILE, "w", encoding="utf-8") as fh:
        fh.write(HOCON_CONTENT + "\n")
    ok(f"Written ({os.path.getsize(TARGET_FILE):,} bytes)")

    step(3, f"Patch {MANIFEST_FILE}")
    if not os.path.isfile(MANIFEST_FILE):
        warn("manifest.hocon not found — creating minimal one")
        with open(MANIFEST_FILE, "w", encoding="utf-8") as fh:
            fh.write('{\n    "generated/ravi_digital_twin_multiagent_system.hocon": true\n}\n')
        ok(f"Created {MANIFEST_FILE}")
    else:
        txt = open(MANIFEST_FILE).read()
        if "ravi_digital_twin_multiagent_system" in txt:
            patched = re.sub(
                r'("generated/ravi_digital_twin_multiagent_system\.hocon"\s*:\s*)false',
                r'\1true', txt)
            if patched != txt:
                open(MANIFEST_FILE, "w").write(patched)
                ok("Changed manifest entry false → true")
            else:
                ok("Manifest entry already true — no change needed")
        else:
            entry = '    "generated/ravi_digital_twin_multiagent_system.hocon": true\n'
            i = txt.rfind("}")
            patched = txt[:i] + entry + txt[i:] if i != -1 else txt + entry
            open(MANIFEST_FILE, "w").write(patched)
            ok("Entry added to manifest.hocon")

    step(4, "Optional pyhocon syntax check")
    try:
        from pyhocon import ConfigFactory
        ConfigFactory.parse_file(TARGET_FILE)
        ok("HOCON parses cleanly")
    except ImportError:
        warn("pyhocon not installed — skipping (pip install pyhocon to enable)")
    except Exception as exc:
        warn(f"HOCON parse error: {exc}")

    print("\n" + "=" * 56)
    print(" DONE. Now restart your NeuroSAN server:")
    print()
    print("   python run_agents.py")
    print("   — or —")
    print("   docker-compose restart")
    print()
    print(" Then refresh your browser.")
    print(" 'rAvI Digital Twin Multiagent System' should")
    print(" appear in Available Agents.")
    print("=" * 56)

if __name__ == "__main__":
    main()
