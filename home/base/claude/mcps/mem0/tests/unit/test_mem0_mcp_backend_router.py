from mem0_mcp_backend_router import MemoryBackendRouter
from mem0_mcp_remote_rest_backend import RemoteMemoryServiceUnavailable


class RecordingBackend:
    def __init__(self, name, healthy=True, fail_on=None):
        self.backend_name = name
        self._healthy = healthy
        self._fail_on = fail_on or set()
        self.calls = []

    def is_healthy(self):
        return self._healthy

    def add(self, text, user_id):
        return self._record("add", text, user_id)

    def search(self, query, user_id, limit):
        return self._record("search", query, user_id, limit)

    def list_memories(self, user_id):
        return self._record("list", user_id)

    def delete(self, memory_id):
        return self._record("delete", memory_id)

    def _record(self, operation, *args):
        self.calls.append((operation, args))
        if operation in self._fail_on:
            raise RemoteMemoryServiceUnavailable(f"{operation} failed")
        return f"{self.backend_name}:{operation}"


def local_factory_returning(backend):
    created = {"count": 0}

    def factory():
        created["count"] += 1
        return backend

    factory.created = created
    return factory


def test_healthy_remote_is_selected_and_local_is_never_built():
    remote = RecordingBackend("remote", healthy=True)
    local = RecordingBackend("local")
    factory = local_factory_returning(local)
    router = MemoryBackendRouter(remote, factory)

    assert router.active_backend_name == "remote"
    assert router.add("note", "lucas") == "remote:add"
    assert factory.created["count"] == 0
    assert local.calls == []


def test_unhealthy_remote_falls_back_to_local_at_startup():
    remote = RecordingBackend("remote", healthy=False)
    local = RecordingBackend("local")
    router = MemoryBackendRouter(remote, local_factory_returning(local))

    assert router.active_backend_name == "local"
    assert router.search("q", "lucas", 5) == "local:search"
    assert local.calls == [("search", ("q", "lucas", 5))]


def test_no_remote_configured_uses_local():
    local = RecordingBackend("local")
    router = MemoryBackendRouter(None, local_factory_returning(local))
    assert router.active_backend_name == "local"
    assert router.list_memories("lucas") == "local:list"


def test_remote_failure_mid_call_degrades_to_local_and_retries():
    remote = RecordingBackend("remote", healthy=True, fail_on={"add"})
    local = RecordingBackend("local")
    router = MemoryBackendRouter(remote, local_factory_returning(local))

    assert router.active_backend_name == "remote"
    result = router.add("note", "lucas")

    assert result == "local:add"
    assert router.active_backend_name == "local"
    assert remote.calls == [("add", ("note", "lucas"))]
    assert local.calls == [("add", ("note", "lucas"))]


def test_remote_health_probe_exception_is_treated_as_unhealthy():
    class ExplodingHealthBackend(RecordingBackend):
        def is_healthy(self):
            raise RuntimeError("network blew up")

    remote = ExplodingHealthBackend("remote")
    local = RecordingBackend("local")
    router = MemoryBackendRouter(remote, local_factory_returning(local))
    assert router.active_backend_name == "local"
