import json

from mem0_mcp_server import build_tool_handlers


class FakeRouter:
    active_backend_name = "local"

    def __init__(self):
        self.calls = []

    def add(self, text, user_id):
        self.calls.append(("add", text, user_id))
        return {"results": [{"id": "1", "memory": text}]}

    def search(self, query, user_id, limit):
        self.calls.append(("search", query, user_id, limit))
        return [{"id": "1", "memory": "hit"}]

    def list_memories(self, user_id):
        self.calls.append(("list", user_id))
        return [{"id": "1", "memory": "all"}]

    def delete(self, memory_id):
        self.calls.append(("delete", memory_id))
        return {"message": "deleted"}


def build(default_user_id="lucas"):
    router = FakeRouter()
    return router, build_tool_handlers(router, default_user_id)


def test_add_memory_uses_default_user_id_and_wraps_envelope():
    router, handlers = build()
    payload = json.loads(handlers["add_memory"]({"text": "remember me"}))
    assert router.calls == [("add", "remember me", "lucas")]
    assert payload["backend"] == "local"
    assert payload["result"]["results"][0]["memory"] == "remember me"


def test_explicit_user_id_overrides_default():
    router, handlers = build()
    handlers["search_memory"]({"query": "q", "user_id": "someone-else"})
    assert router.calls == [("search", "q", "someone-else", 5)]


def test_search_memory_defaults_and_coerces_limit():
    router, handlers = build()
    handlers["search_memory"]({"query": "q"})
    handlers["search_memory"]({"query": "q2", "limit": "9"})
    assert router.calls[0] == ("search", "q", "lucas", 5)
    assert router.calls[1] == ("search", "q2", "lucas", 9)


def test_list_memories_returns_results_envelope():
    router, handlers = build()
    payload = json.loads(handlers["list_memories"]({}))
    assert payload["results"] == [{"id": "1", "memory": "all"}]


def test_delete_memory_passes_memory_id():
    router, handlers = build()
    payload = json.loads(handlers["delete_memory"]({"memory_id": "abc"}))
    assert router.calls == [("delete", "abc")]
    assert payload["result"]["message"] == "deleted"


def test_missing_required_text_raises_so_protocol_layer_reports_error():
    _, handlers = build()
    try:
        handlers["add_memory"]({})
    except KeyError:
        return
    raise AssertionError("expected KeyError for missing required 'text'")
