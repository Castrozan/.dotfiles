import json

import pytest

pytest.importorskip("mcp")

import mem0_mcp_server as server


class FakeRouter:
    def __init__(self):
        self.active_backend_name = "local"
        self.calls = []

    def add(self, text, user_id):
        self.calls.append(("add", text, user_id))
        return {"results": [{"id": "1", "memory": text}]}

    def search(self, query, user_id, limit):
        self.calls.append(("search", query, user_id, limit))
        return [{"id": "1"}]

    def list_memories(self, user_id):
        self.calls.append(("list", user_id))
        return [{"id": "1"}]

    def delete(self, memory_id):
        self.calls.append(("delete", memory_id))
        return {"message": "deleted"}


@pytest.fixture
def fake_router(monkeypatch):
    router = FakeRouter()
    monkeypatch.setattr(server, "router", router)
    return router


def test_add_memory_defaults_user_and_wraps_backend_envelope(fake_router):
    payload = json.loads(server.add_memory("remember me"))
    assert fake_router.calls == [("add", "remember me", "lucas")]
    assert payload["backend"] == "local"
    assert payload["result"]["results"][0]["memory"] == "remember me"


def test_explicit_user_id_overrides_default(fake_router):
    server.search_memory("q", user_id="someone")
    assert fake_router.calls == [("search", "q", "someone", 5)]


def test_search_limit_passes_through(fake_router):
    server.search_memory("q", limit=9)
    assert fake_router.calls[0] == ("search", "q", "lucas", 9)


def test_list_and_delete_envelopes(fake_router):
    assert json.loads(server.list_memories())["results"] == [{"id": "1"}]
    assert json.loads(server.delete_memory("abc"))["result"]["message"] == "deleted"
    assert ("delete", "abc") in fake_router.calls
