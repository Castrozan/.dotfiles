import pytest

pytest.importorskip("mem0")
pytest.importorskip("chromadb")
pytest.importorskip("sentence_transformers")

from mem0_mcp_local_embedded_backend import LocalEmbeddedMemoryBackend


def build_backend(tmp_path):
    return LocalEmbeddedMemoryBackend(
        store_directory=str(tmp_path / "store"),
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        collection_name="e2e_test",
    )


def test_add_then_search_recalls_stored_memory(tmp_path):
    backend = build_backend(tmp_path)
    backend.add(
        "Lucas prefers concise status reports with Done and Next lines.", "lucas"
    )
    backend.add("The fallback uses chroma plus a CPU MiniLM embedder.", "lucas")

    results = backend.search("how should replies be formatted", "lucas", 3)
    recalled = " ".join(item["memory"] for item in results).lower()
    assert "concise" in recalled


def test_list_memories_returns_everything_for_user(tmp_path):
    backend = build_backend(tmp_path)
    backend.add("first memory", "lucas")
    backend.add("second memory", "lucas")
    listed = backend.list_memories("lucas")
    assert len(listed) == 2


def test_add_does_not_require_an_llm_credential(tmp_path):
    backend = build_backend(tmp_path)
    stored = backend.add("no llm needed for this add", "lucas")
    assert stored["results"][0]["memory"] == "no llm needed for this add"


def test_memories_are_scoped_per_user(tmp_path):
    backend = build_backend(tmp_path)
    backend.add("lucas owns a macbook named kira", "lucas")
    backend.add("someone else owns a different machine entirely", "other-user")

    lucas_listed = backend.list_memories("lucas")
    assert len(lucas_listed) == 1
    assert lucas_listed[0]["memory"] == "lucas owns a macbook named kira"

    lucas_search = backend.search("who owns kira", "lucas", 5)
    assert all(item["user_id"] == "lucas" for item in lucas_search)
    assert any("kira" in item["memory"] for item in lucas_search)
