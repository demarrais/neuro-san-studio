"""Tests for explicit Chroma paths in the rAvI memory query tool."""

import importlib
import sys
import types


class FakeCollection:
    def __init__(self, name):
        self.name = name
        self.records = [
            {
                "id": f"{name}-1",
                "document": f"Document from {name}",
                "metadata": {"source": name},
                "distance": 0.1,
            }
        ]

    def count(self):
        return len(self.records)

    def query(self, query_texts, n_results, include):
        del query_texts, include
        selected = self.records[:n_results]
        return {
            "ids": [[record["id"] for record in selected]],
            "documents": [[record["document"] for record in selected]],
            "metadatas": [[record["metadata"] for record in selected]],
            "distances": [[record["distance"] for record in selected]],
        }


class FakeClient:
    def __init__(self, path, settings):
        del settings
        self.path = path
        self.collections = {}

    def get_or_create_collection(self, name):
        self.collections.setdefault(name, FakeCollection(name))
        return self.collections[name]

    def list_collections(self):
        return list(self.collections.values())


created_clients = []


def _persistent_client(path, settings):
    client = FakeClient(path, settings)
    created_clients.append(client)
    return client


def _install_runtime_stubs() -> dict[str, types.ModuleType | None]:
    neuro_san = types.ModuleType("neuro_san")
    interfaces = types.ModuleType("neuro_san.interfaces")
    coded_tool = types.ModuleType("neuro_san.interfaces.coded_tool")

    class CodedTool:
        pass

    coded_tool.CodedTool = CodedTool

    chromadb = types.ModuleType("chromadb")
    chromadb.PersistentClient = _persistent_client
    chromadb_config = types.ModuleType("chromadb.config")

    class Settings:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    chromadb_config.Settings = Settings
    replacements = {
        "neuro_san": neuro_san,
        "neuro_san.interfaces": interfaces,
        "neuro_san.interfaces.coded_tool": coded_tool,
        "chromadb": chromadb,
        "chromadb.config": chromadb_config,
    }
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
    memory_module = importlib.import_module(
        "coded_tools.generated.ravi_memory.memory_query_tool"
    )
finally:
    _restore_runtime_stubs(_previous_modules)

MemoryQueryTool = memory_module.MemoryQueryTool


def test_explicit_paths_create_independent_clients(tmp_path):
    created_clients.clear()
    memory_module._clients.clear()
    tool = MemoryQueryTool()
    voice_path = tmp_path / "voice"
    evidence_path = tmp_path / "evidence"

    voice_result = tool.invoke(
        {
            "query": "voice",
            "collection": "ravi_voice_primary",
            "path": str(voice_path),
            "top_k": 3,
        }
    )
    evidence_result = tool.invoke(
        {
            "query": "topic",
            "collection": "ravi_voice_knowledge",
            "path": str(evidence_path),
            "top_k": 3,
        }
    )

    assert voice_result["status"] == "OK"
    assert evidence_result["status"] == "OK"
    assert voice_result["path"] != evidence_result["path"]
    assert len(created_clients) == 2
    assert {client.path for client in created_clients} == {
        str(voice_path.resolve()),
        str(evidence_path.resolve()),
    }


def test_same_path_reuses_cached_client(tmp_path):
    created_clients.clear()
    memory_module._clients.clear()
    tool = MemoryQueryTool()
    path = tmp_path / "shared"

    tool.invoke({"query": "one", "collection": "first", "path": str(path)})
    tool.invoke({"query": "two", "collection": "second", "path": str(path)})

    assert len(created_clients) == 1
    assert set(created_clients[0].collections) == {"first", "second"}


def test_form_d_wrapper_and_explicit_path(tmp_path):
    created_clients.clear()
    memory_module._clients.clear()
    tool = MemoryQueryTool()
    path = tmp_path / "wrapped"

    result = tool.invoke(
        {
            "args": {
                "query": "voice",
                "collection": "ravi_voice_primary",
                "path": str(path),
            },
            "origin": ["publisher"],
        }
    )

    assert result["status"] == "OK"
    assert result["path"] == str(path.resolve())
    assert result["collection"] == "ravi_voice_primary"
