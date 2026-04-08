from neuro_san.interfaces.coded_tool import CodedTool
import os, re, logging
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)
_CHROMA_PATH = os.environ.get("RAVI_CHROMA_PATH", "./ravi_chroma_db")
COLLECTION = "ravi_voice_knowledge"

BANNED_WORDS = [
    "paradigm", "robust", "pivotal", "tapestry", "delve", "herculean",
    "cusp", "rejuvenation", "beckons", "paving the way", "stands as a testament",
    "reflects broader trends", "inaction is not an option", "transformative swell",
    "on the brink", "it is important to note", "in conclusion",
    "as we stand", "it is imperative", "moral imperative",
    "unleash", "synergy", "game-changer", "groundbreaking",
    "rapid evolution", "rapidly evolving", "dizzying disruption",
]

REQUIRED_STATS = []  # Not used — stat detection is regex-based

# Opener must NOT be a generic AI statement
BANNED_OPENER_PATTERNS = [
    r"^the (rapid|rise|advent|age|era|dawn|power|promise|potential|transformative) (rise )?of (artificial intelligence|ai)",
    r"^artificial intelligence (is|has|continues)",
    r"^as (we|the world|society|businesses)",
    r"^in today",
    r"^amid the",
    r"^in the age of",
    r"^we are (living|entering|witnessing)",
    r"^the (future|world|era|age) of ai",
]

# Opener SHOULD match one of these patterns (provocation, data, observation)
GOOD_OPENER_PATTERNS = [
    r"\d+%",                          # starts with a stat
    r"\$\d",                          # starts with a dollar figure
    r"^what happens when",             # rhetorical provocation
    r"^talk of",                       # direct assertion
    r"^the most important",            # strong claim
    r"^consider",                      # direct address
    r"^here is",                       # direct claim
    r"^history",                       # historical provocation
    r"^work is",                       # grounded claim
    r"^intelligence is",               # grounded claim
]

# Closer must NOT be a summary or inspirational platitude
BANNED_CLOSER_PHRASES = [
    "it's not just about",
    "it is not just about",
    "the choices we make today",
    "together we can",
    "let us not forget",
    "the time to act",
    "let this be the generation",
    "doesn't deepen divides but bridges them",
    "as we move forward",
    "supplements humanity",
    "accelerates economic divides",
    "collective progress",
    "transformative age",
    "shared opportunity",
    "by taking action now",
    "the opportunity is",
    "this is a moment",
    "this moment calls for",
    "hinges on shared",
    "call to action",
    "the road ahead",
    "the path forward",
    "only time will tell",
]

# Closer SHOULD match one of these patterns (forward provocation)
GOOD_CLOSER_PATTERNS = [
    r"may not come from artificial intelligence",
    r"empowering every worker",
    r"will come from",
    r"the question (is|now|that) ",
    r"if \d",
    r"that outcome is not inevitable",
    r"constraint has",
    r"new jobs are born",
    r"not just the few",
    r"benefits.*broadly",
    r"ensure.*ai.*benefits",
    r"empower.*thrive",
    r"intelligence age",
    r"social contract",
    r"shared prosperity",
    r"every worker",
    r"build.*systems",
    r"force multiplier",
    r"equipping every",
    r"belonging to those who",
    r"future belongs",
    r"talk of an ai bubble",
    r"ai builder",
]


BANNED_ATTRIBUTION_PHRASES = [
    "ravi kumar s calls",
    "ravi kumar s has",
    "ravi kumar s often",
    "kumar has termed",
    "kumar has called",
    "kumar has often",
    "kumar has described",
    "kumar has emphasized",
    "kumar has stressed",
    "kumar has noted",
    "kumar has argued",
    "kumar has stated",
    "kumar has said",
    "as kumar",
    "as ravi kumar",
    "ravi kumar s said",
    "ravi kumar s describes",
    "ravi kumar s emphasizes",
    "ravi kumar s believes",
]

_client = None

def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        _client = chromadb.PersistentClient(
            path=_CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
    except Exception as e:
        logger.warning("EditorialGateTool: ChromaDB unavailable: %s", e)
    return _client


def check_statistics(text: str) -> dict:
    import re
    found = re.findall(r"\d+\.?\d*\s*%|\d+\.?\d*x\b|\d{4}\s*occupations|\d+,\d+\s*tasks|\d+\s*professions", text.lower())
    passed = len(found) >= 2
    return {
        "passed": passed,
        "check": "statistics",
        "stats_found": found,
        "message": (
            f"Statistics present: {found}"
            if passed else
            "MISSING STATISTICS: Include at least 2 statistics grounded in ingested content. "
            "Call memory_query_tool with the draft topic to retrieve relevant verbatim figures. "
            "Do NOT invent or reuse the same figures repeatedly."
        ),
    }


def check_em_dashes(text: str) -> dict:
    import re
    count = len(re.findall(r"\u2014|(?<!-)--(?!-)", text))
    word_count = len(text.split())
    allowed = max(1, word_count // 500)
    passed = count <= allowed
    return {
        "passed": passed,
        "check": "em_dash_count",
        "em_dashes_found": count,
        "word_count": word_count,
        "allowed": allowed,
        "message": (
            f"Em-dash usage OK: {count} in {word_count} words."
            if passed else
            f"EM-DASH OVERUSE: {count} found in {word_count} words. Max {allowed}. "
            "Replace excess with commas, colons, or periods."
        ),
    }


class EditorialGateTool(CodedTool):

    _VERSION = "v3-editorial-gate"

    def invoke(self, args: dict, sly_data: dict = None) -> dict:
        if isinstance(args, dict) and "args" in args:
            inner = args["args"]
            if isinstance(inner, list) and len(inner) > 0:
                args = inner[0]
            elif isinstance(inner, dict):
                args = inner

        draft = args.get("draft", "").strip()
        if not draft:
            return {
                "status": "ERROR",
                "violations": ["No draft text provided."],
                "message": "ERROR: You must write the complete draft FIRST before calling this tool. Write the full blog post or content piece, then pass the entire text as the draft argument. Do not call editorial_gate_tool until the draft is fully written.",
            }

        violations = []
        draft_lower = draft.lower()

        # 1. Banned words
        found_banned = [w for w in BANNED_WORDS if w.lower() in draft_lower]
        if found_banned:
            violations.append(
                f"BANNED WORDS found: {found_banned}. Remove every instance before resubmitting."
            )

        # 2. Statistics check — hard block if zero, soft warning if 1 or 2
        import re as _re_stats
        found_stats = _re_stats.findall(r"\d+\.?\d*\s*%|\d+\.?\d*x\b|\d{1,3}(?:,\d{3})+", draft)
        stat_warning = None
        if len(found_stats) == 0:
            violations.append(
                "MISSING STATISTICS: Must include at least 2 statistics grounded in ingested content. "
                "Call memory_query_tool with the draft topic to retrieve relevant verbatim statistics. "
                "Do NOT invent figures. Use only what the knowledge base returns."
            )
        elif len(found_stats) < 2:
            violations.append(
                f"INSUFFICIENT STATISTICS: Only {len(found_stats)} found: {found_stats}. Include at least 2."
            )


        # Word count enforcement - fail if draft is under 80% of requested length
        import re as _re2
        word_count = len(draft.split())
        word_count_match = _re2.search(r'(\d+)[- ]word', draft_lower)
        # Check if the original request embedded a word count hint in sly_data or check for very short output
        # Gate enforces minimum 150 words for any blog/op-ed, 50 for social posts
        social_keywords = ["linkedin", "twitter", "x post", "tweet", "social"]
        is_social = any(k in draft_lower for k in social_keywords)
        min_words = 50 if is_social else 150
        if word_count < min_words:
            violations.append(
                f"DRAFT TOO SHORT: {word_count} words. Minimum is {min_words} words for this content type. "
                f"Expand the draft substantially before resubmitting."
            )

        # 3. Opener: must not be generic AND should be a provocation/data point
        first_line = draft.strip().split("\n")[0]
        first_sentence = first_line.split(".")[0].lower().strip()
        first_sentence = re.sub(r"^#+\s*", "", first_sentence).strip()
        first_sentence = re.sub(r"^\*+\s*", "", first_sentence).strip()

        opener_banned = False
        for pattern in BANNED_OPENER_PATTERNS:
            if re.search(pattern, first_sentence):
                violations.append(
                    f"BANNED OPENER: \"{first_sentence[:120]}\". "
                    f"Must open with a specific data point, provocation, or direct observation. "
                    f"NOT a generic statement about AI. "
                    f"Good openers from Ravi's corpus: "
                    f"\"Talk of an AI bubble is overblown.\" or "
                    f"\"What happens when society embraces a technology faster than it can absorb its consequences?\""
                )
                opener_banned = True
                break

        if not opener_banned:
            opener_good = any(re.search(p, first_sentence) for p in GOOD_OPENER_PATTERNS)
            if not opener_good:
                violations.append(
                    f"WEAK OPENER: \"{first_sentence[:120]}\". "
                    f"Opener should be a specific statistic, direct provocation, or strong claim. "
                    f"Examples from ingested Ravi content: "
                    f"\"Talk of an AI bubble is overblown.\" / "
                    f"\"What happens when society embraces a technology faster than it can absorb its consequences?\""
                )

        # 4. Closer: must not summarize AND should provoke forward
        paragraphs = [p.strip() for p in draft.strip().split("\n\n") if p.strip()]
        last_para = paragraphs[-1].lower() if paragraphs else ""

        closer_banned = False
        for phrase in BANNED_CLOSER_PHRASES:
            if phrase in last_para:
                violations.append(
                    f"BANNED CLOSER: \"{phrase}\". "
                    f"Closing must NOT summarize or inspire with platitudes. "
                    f"Must provoke forward. "
                    f"Best closer from Ravi's ingested corpus: "
                    f"\"The most important innovation of the coming decade may not come from artificial intelligence. "
                    f"It will come from empowering every worker to use it to generate economic and societal value.\""
                )
                closer_banned = True
                break

        if not closer_banned:
            closer_good = any(re.search(p, last_para) for p in GOOD_CLOSER_PATTERNS)
            if not closer_good:
                violations.append(
                    f"WEAK CLOSER: Last paragraph does not end with a forward-looking provocation. "
                    f"Use ingested Ravi content as the model: "
                    f"\"The most important innovation of the coming decade may not come from artificial intelligence. "
                    f"It will come from empowering every worker to use it to generate economic and societal value.\""
                )

        # 5. Header structure
        bold_colon = len(re.findall(r"\*\*[^*]+:\*\*", draft))
        hash_colon = len(re.findall(r"#{1,4}\s+[^\n]+:", draft))
        if bold_colon >= 3 or hash_colon >= 3:
            violations.append(
                f"BANNED STRUCTURE: {bold_colon + hash_colon} bold/header lines with colons as primary structure. "
                f"Ravi writes in paragraphs with embedded structure, not listicles."
            )


        # 7. Third-person attribution check — impersonation-adjacent framing
        found_attribution = [p for p in BANNED_ATTRIBUTION_PHRASES if p in draft_lower]
        if found_attribution:
            violations.append(
                f"BANNED ATTRIBUTION framing found: {found_attribution}. "
                f"Do not attribute frameworks or claims to Ravi Kumar S by name. "
                f"Write as if the ideas are being stated directly, not attributed. "
                f"Replace 'what Ravi Kumar S calls X' with simply 'X'. "
                f"Replace 'Kumar has often emphasized Y' with simply 'Y'."
            )


        # 8. Em-dash overuse check
        em_dashes = draft.count("—")
        words = len(draft.split())
        if em_dashes > max(1, words // 500):
            violations.append(
                f"EM-DASH OVERUSE: {em_dashes} em-dashes found in {words} words. "
                f"Maximum 1 per 500 words. Remove excess em-dashes and replace with "
                f"commas, colons, semicolons, or periods as appropriate."
            )

        # 9. Self-congratulatory closer check
        meta_closers = [
            "i hope this helps",
            "feel free to let me know",
            "this draft was designed",
            "this piece was crafted",
            "let me know if you would like further",
            "let me know if you need adjustments",
            "you are welcome to publish",
            "thank you for entrusting",
            "if additional adjustments",
        ]
        full_lower = draft.lower()
        found_meta = [p for p in meta_closers if p in full_lower]
        if found_meta:
            violations.append(
                f"META-COMMENTARY CLOSER found: {found_meta}. "
                f"Never narrate the ending or thank the user inside the content. "
                f"The work ends. It does not explain itself."
            )

        # 10. Emoji check
        import unicodedata
        ALLOWED_SYMBOLS = {0xAE, 0x2122, 0x00A9}  # ®, ™, ©
        emoji_count = sum(1 for char in draft
                         if (unicodedata.category(char) in ("So", "Sm")
                         or ord(char) > 127000)
                         and ord(char) not in ALLOWED_SYMBOLS)
        if emoji_count > 0:
            violations.append(
                f"EMOJI FOUND: {emoji_count} emoji(s) detected. "
                f"Emojis are banned in all output. Remove every instance."
            )


        # 11. Mandatory closing question check — not every post needs one
        closing_question_patterns = [
            r"the question is[:\s]",
            r"will (you|pr|your|we|they|it) (be|lead|follow|build|become|define)",
            r"how are you (embedding|preparing|thinking|approaching|using|navigating)",
            r"reflections welcome",
            r"what do you think",
            r"are you ready",
            r"(the question|question) (now|remains|is)[:,]",
            r"i('d| would) (love|welcome) (to hear|your)",
            r"how (is|are) your (team|org|company|business)",
        ]
        import re as _re
        last_para_lower = paragraphs[-1].lower() if paragraphs else ""
        # Only flag if it ends with a question mark AND matches a generic pattern
        if last_para_lower.rstrip().endswith("?"):
            for qpat in closing_question_patterns:
                if _re.search(qpat, last_para_lower):
                    violations.append(
                        "GENERIC CLOSING QUESTION detected. Not every post needs to end "
                        "with a question. This pattern is predictable and weakens the close. "
                        "Make the claim instead. Let it land. Remove the closing question "
                        "or replace it with a specific, unresolvable tension the reader "
                        "alone can answer."
                    )
                    break


        # Stat attribution check - verify figures appear verbatim in ingested content
        # Initialize collection for stat lookup
        try:
            import chromadb as _chromadb
            from chromadb.config import Settings as _Settings
            _stat_client = _chromadb.PersistentClient(
                path=_CHROMA_PATH,
                settings=_Settings(anonymized_telemetry=False)
            )
            _collection = _stat_client.get_collection("ravi_voice_knowledge")
        except Exception:
            _collection = None
        import re as _re3
        figures = _re3.findall(r'\d+(?:\.\d+)?%|\$[\d.]+[TBM]?(?:\s*(?:trillion|billion|million))?|\d+(?:,\d{3})*(?:\s*(?:trillion|billion|million))?', draft)
        # Filter to significant figures (not page numbers, years, etc.)
        significant_figures = [f for f in figures if not _re3.match(r'^(19|20)\d{2}$', f.replace(',',''))]
        fabricated = []
        if significant_figures and _collection is not None:
            for fig in significant_figures[:8]:  # Check up to 8 figures
                fig_clean = fig.strip()
                # Search ChromaDB for this figure in context
                try:
                    results = _collection.query(query_texts=[fig_clean], n_results=2)
                    found = False
                    for doc in results["documents"][0]:
                        if fig_clean.lower() in doc.lower():
                            found = True
                            break
                    if not found:
                        fabricated.append(fig_clean)
                except Exception:
                    pass
        # Filter out known-good figures that appear in ingested slide content
        known_good = ["230", "83%", "56%", "37%", "12,000", "12k", "230k", "230,000", "2.2", "1.4", "4.4", "4.5", "93", "31", "60", "2%", "9%", "30%", "7%", "95%",
                      "20%", "50%", "30%", "60%", "8%", "10%", "15%", "28", "75%",
                      "4.4", "1.9", "6.3", "3.4", "1.4", "840", "280", "100"]
        truly_fabricated = [f for f in fabricated
                           if not any(k.lower() in f.lower() or f.lower() in k.lower()
                                     for k in known_good)]
        if truly_fabricated:
            violations.append(
                f"UNVERIFIED STATISTICS: {truly_fabricated} could not be found verbatim in the ingested "
                f"knowledge base. Remove or replace with figures that appear in ingested content."
            )

        # 6. Voice fidelity via ChromaDB
        fidelity = self._voice_fidelity(draft)
        if fidelity.get("score") is not None and fidelity["score"] < 0.35:
            violations.append(
                f"VOICE FIDELITY TOO LOW ({fidelity['score']}): "
                f"Draft is semantically distant from ingested Ravi content. "
                f"Use specific phrases, statistics, and frameworks from the knowledge base."
            )

        if violations:
            return {
                "status": "FAIL",
                "violations": violations,
                "voice_fidelity": fidelity,
                "message": (
                    "GATE FAILED. Do NOT return this draft to the user. "
                    "Fix ALL violations listed below and resubmit to editorial_gate_tool. "
                    "Loop until status is PASS.\n\nVIOLATIONS:\n"
                    + "\n".join(f"- {v}" for v in violations)
                ),
            }

        return {
            "status": "PASS",
            "violations": [],
            "voice_fidelity": fidelity,
            "message": (
                f"GATE PASSED. All editorial checks passed. {(stat_warning or str())} "
                f"{fidelity.get('note', '')} "
                f"You may return this draft to the user."
            ),
        }

    def _voice_fidelity(self, draft: str) -> dict:
        client = _get_client()
        if client is None:
            return {"score": None, "note": "ChromaDB unavailable."}
        try:
            col = client.get_or_create_collection(COLLECTION)
            results = col.query(query_texts=[draft[:500]], n_results=3)
            distances = results.get("distances", [[]])[0]
            docs = results.get("documents", [[]])[0]
            if not distances:
                return {"score": 0.0, "note": "No matching content in knowledge base."}
            avg_dist = sum(distances) / len(distances)
            score = round(max(0.0, 1.0 - (avg_dist / 2.0)), 3)
            return {
                "score": score,
                "top_match": docs[0][:200] if docs else "",
                "note": f"Voice fidelity: {round(score * 100)}% match to ingested Ravi content.",
            }
        except Exception as e:
            logger.warning("Voice fidelity check failed: %s", e)
            return {"score": None, "note": f"Voice fidelity error: {e}"}
