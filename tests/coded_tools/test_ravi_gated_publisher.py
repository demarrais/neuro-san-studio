"""Focused tests for the code-owned rAvI publisher control loop."""

import asyncio
import importlib
import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock


def _install_runtime_stubs() -> dict[str, types.ModuleType | None]:
    replacements: dict[str, types.ModuleType] = {}

    neuro_san = types.ModuleType("neuro_san")
    interfaces = types.ModuleType("neuro_san.interfaces")
    coded_tool = types.ModuleType("neuro_san.interfaces.coded_tool")

    class CodedTool:
        pass

    coded_tool.CodedTool = CodedTool
    replacements.update(
        {
            "neuro_san": neuro_san,
            "neuro_san.interfaces": interfaces,
            "neuro_san.interfaces.coded_tool": coded_tool,
        }
    )

    try:
        import dotenv  # noqa: F401
    except ImportError:
        dotenv_module = types.ModuleType("dotenv")

        def load_dotenv(**_):
            return False

        dotenv_module.load_dotenv = load_dotenv
        replacements["dotenv"] = dotenv_module

    previous = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    return previous


def _restore_runtime_stubs(previous: dict[str, types.ModuleType | None]) -> None:
    for name, original in previous.items():
        if original is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = original


_previous_modules = _install_runtime_stubs()
try:
    publisher_module = importlib.import_module(
        "coded_tools.generated.ravi_memory.ravi_gated_publisher"
    )
finally:
    _restore_runtime_stubs(_previous_modules)

RaviGatedPublisher = publisher_module.RaviGatedPublisher


class FakeMemory:
    def __init__(self, voice_documents=None, evidence_documents=None):
        self.voice_documents = voice_documents or []
        self.evidence_documents = evidence_documents or []
        self.calls = []

    def invoke(self, payload):
        self.calls.append(dict(payload))
        if payload["collection"] == "ravi_voice_primary":
            documents = self.voice_documents
        else:
            documents = self.evidence_documents
        return {
            "status": "OK" if documents else "EMPTY",
            "documents": documents,
            "count": len(documents),
            "collection": payload["collection"],
            "path": payload["path"],
        }


class FakeGate:
    def __init__(self, reports=None):
        self.reports = list(
            reports
            or [
                {
                    "status": "PASS",
                    "gate_passed": True,
                    "violations": [],
                }
            ]
        )
        self.calls = []

    def invoke(self, payload):
        self.calls.append(dict(payload))
        index = min(len(self.calls) - 1, len(self.reports) - 1)
        return dict(self.reports[index])


def _azure_client(*drafts):
    responses = [
        SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=draft))]
        )
        for draft in drafts
    ]
    create = AsyncMock(side_effect=responses)
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    return client, create


def _run(publisher, args):
    return asyncio.run(publisher.async_invoke(args))


def _voice_document():
    return {
        "id": "voice-1",
        "content": (
            "The reality is that an AI builder must reforge the first principles "
            "of delivery. In an older example, 93% was cited."
        ),
        "metadata": {
            "source": "Ravi transcript",
            "speaker": "Ravi Kumar S",
            "authorship": "verbatim",
        },
        "relevance": 0.96,
    }


def _evidence_document(
    content="Revenue reached $5.41 billion, up 5.8% year over year.",
):
    return {
        "id": "evidence-1",
        "content": content,
        "metadata": {
            "source": "Approved results release",
            "external_use": True,
        },
        "relevance": 0.93,
    }


def test_retrieves_separate_lanes_and_returns_evidence_packet(monkeypatch):
    monkeypatch.delenv("RAVI_VOICE_PRIMARY_CHROMA_PATH", raising=False)
    monkeypatch.delenv("RAVI_VOICE_KNOWLEDGE_CHROMA_PATH", raising=False)
    monkeypatch.delenv("RAVI_CHROMA_PATH", raising=False)

    memory = FakeMemory([_voice_document()], [_evidence_document()])
    gate = FakeGate()
    client, create = _azure_client(
        "Revenue reached $5.41 billion, up 5.8% year over year. "
        "That progress will define what comes next."
    )
    publisher = RaviGatedPublisher(
        memory_tool=memory,
        gate_tool=gate,
        azure_client=client,
    )

    result = _run(
        publisher,
        {"request": "Draft a short results post.", "content_type": "social"},
    )

    assert result["status"] == "PASS"
    assert result["publish"] is True
    assert result["evidence_packet"]["lanes"]["authentic_voice"]["role"] == (
        "style_only"
    )
    assert result["evidence_packet"]["lanes"]["topic_evidence"]["role"] == (
        "factual_support"
    )
    assert result["evidence_packet"]["allowed_numeric_tokens"] == [
        "$5.41 billion",
        "5.8%",
    ]
    assert [call["collection"] for call in memory.calls] == [
        "ravi_voice_primary",
        "ravi_voice_knowledge",
    ]
    assert memory.calls[0]["path"].endswith("/chroma_db")
    assert memory.calls[1]["path"].endswith("/ravi_chroma_db")

    system_prompt = create.await_args.kwargs["messages"][0]["content"]
    assert "Use your knowledge" not in system_prompt
    assert "The following Q1 2026 figures" not in system_prompt
    assert "$4.4 trillion" not in system_prompt
    assert "18,000" not in system_prompt
    assert gate.calls[0]["content_type"] == "social"


def test_empty_topic_evidence_fails_closed_without_calling_azure():
    memory = FakeMemory([_voice_document()], [])
    gate = FakeGate()
    client, create = _azure_client("This must never be used.")
    publisher = RaviGatedPublisher(
        memory_tool=memory,
        gate_tool=gate,
        azure_client=client,
    )

    result = _run(
        publisher,
        {"request": "Draft a post about an unsupported topic."},
    )

    assert result["status"] == "EVIDENCE_GAP"
    assert result["draft"] is None
    assert result["suppressed_draft"] is True
    assert result["publish"] is False
    assert create.await_count == 0
    assert gate.calls == []
    assert result["evidence_packet"]["policy"]["general_knowledge_fallback"] is False


def test_empty_voice_lane_fails_closed_without_calling_azure():
    memory = FakeMemory([], [_evidence_document()])
    gate = FakeGate()
    client, create = _azure_client("This must never be used.")
    publisher = RaviGatedPublisher(
        memory_tool=memory,
        gate_tool=gate,
        azure_client=client,
    )

    result = _run(publisher, {"request": "Draft a results post."})

    assert result["status"] == "VOICE_EVIDENCE_GAP"
    assert result["draft"] is None
    assert result["suppressed_draft"] is True
    assert result["publish"] is False
    assert create.await_count == 0
    assert gate.calls == []


def test_unsupported_number_retries_instead_of_replacing_it():
    memory = FakeMemory(
        [_voice_document()],
        [_evidence_document("The verified adoption rate is 56%.")],
    )
    gate = FakeGate()
    client, create = _azure_client(
        "The adoption rate is 37%. That shift will define the future.",
        "The adoption rate is 56%. That shift will define the future.",
    )
    publisher = RaviGatedPublisher(
        memory_tool=memory,
        gate_tool=gate,
        azure_client=client,
    )

    result = _run(
        publisher,
        {"request": "Draft an adoption post.", "max_attempts": 2},
    )

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert result["draft"] == (
        "The adoption rate is 56%. That shift will define the future."
    )
    assert "a significant portion" not in result["draft"]
    assert create.await_count == 2
    assert len(gate.calls) == 2
    second_user_prompt = create.await_args_list[1].kwargs["messages"][1]["content"]
    assert "37%" in second_user_prompt
    assert "UNSUPPORTED NUMBERS" in second_user_prompt


def test_final_gate_failure_suppresses_draft_but_keeps_packet():
    memory = FakeMemory(
        [_voice_document()],
        [_evidence_document("The study reports 56% and 50%.")],
    )
    failure = {
        "status": "GATE_FAILURE",
        "gate_passed": False,
        "violations": ["Closer does not meet the editorial standard."],
        "checks": [],
    }
    gate = FakeGate([failure])
    client, create = _azure_client(
        "The study reports 56% and 50%.",
        "The study reports 56% and 50%.",
    )
    publisher = RaviGatedPublisher(
        memory_tool=memory,
        gate_tool=gate,
        azure_client=client,
    )

    result = _run(
        publisher,
        {"request": "Draft a study post.", "max_attempts": 2},
    )

    assert result["status"] == "GATE_FAILURE"
    assert result["publish"] is False
    assert result["draft"] is None
    assert result["suppressed_draft"] is True
    assert result["attempts"] == 2
    assert result["evidence_packet"]["lanes"]["topic_evidence"]["matches"]
    assert create.await_count == 2


def test_gate_exception_suppresses_draft_and_returns_packet():
    class FailingGate:
        def invoke(self, payload):
            del payload
            raise RuntimeError("gate unavailable")

    memory = FakeMemory([_voice_document()], [_evidence_document()])
    client, create = _azure_client(
        "Revenue reached $5.41 billion, up 5.8% year over year."
    )
    publisher = RaviGatedPublisher(
        memory_tool=memory,
        gate_tool=FailingGate(),
        azure_client=client,
    )

    result = _run(publisher, {"request": "Draft a results post."})

    assert result["status"] == "ERROR"
    assert result["draft"] is None
    assert result["suppressed_draft"] is True
    assert result["error_type"] == "RuntimeError"
    assert result["evidence_packet"]["lanes"]["topic_evidence"]["matches"]
    assert create.await_count == 1


def test_transport_sanitization_does_not_mutate_generated_draft():
    evidence = _evidence_document(
        "The source describes a cusp of change and cites $650 billion and "
        "10,000 automation use cases."
    )
    expected = (
        "We are at the cusp of change, with $650 billion and 10,000 automation "
        "use cases in view."
    )
    memory = FakeMemory([_voice_document()], [evidence])
    gate = FakeGate()
    client, _ = _azure_client(expected)
    publisher = RaviGatedPublisher(
        memory_tool=memory,
        gate_tool=gate,
        azure_client=client,
    )

    result = _run(
        publisher,
        {"request": "Draft a post using the supplied evidence."},
    )

    assert result["status"] == "PASS"
    assert result["draft"] == expected
    assert "threshold" not in result["draft"]
    assert "$4.4 trillion" not in result["draft"]


def test_caller_supplied_facts_can_fill_empty_retrieval_lane():
    memory = FakeMemory([_voice_document()], [])
    gate = FakeGate()
    client, create = _azure_client(
        "The approved figure is 42%. That discipline will define execution."
    )
    publisher = RaviGatedPublisher(
        memory_tool=memory,
        gate_tool=gate,
        azure_client=client,
    )

    result = _run(
        publisher,
        {
            "request": "Draft a short post.",
            "canonical_facts": "The approved figure is 42%.",
        },
    )

    assert result["status"] == "PASS"
    assert result["evidence_packet"]["allowed_numeric_tokens"] == ["42%"]
    assert create.await_count == 1


def test_wrapped_neurosan_args_are_unwrapped():
    memory = FakeMemory([_voice_document()], [_evidence_document("Approved: 42%.")])
    gate = FakeGate()
    client, _ = _azure_client("Approved: 42%.")
    publisher = RaviGatedPublisher(
        memory_tool=memory,
        gate_tool=gate,
        azure_client=client,
    )

    result = _run(
        publisher,
        {
            "tool_args": {
                "args": [
                    {
                        "request": "Draft a short post.",
                        "content_type": "social",
                    }
                ],
                "origin": ["top_agent"],
            }
        },
    )

    assert result["status"] == "PASS"
    assert result["evidence_packet"]["request"] == "Draft a short post."
    assert gate.calls[0]["content_type"] == "social"
