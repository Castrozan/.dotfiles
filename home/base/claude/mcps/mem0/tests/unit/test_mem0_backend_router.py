from mem0_backend_router import MemoryBackendRouter
from mem0_memory_backends import RemoteUnavailable


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
            raise RemoteUnavailable(f"{operation} failed")
        return f"{self.backend_name}:{operation}"


def lazy(backend):
    state = {"built": 0}

    def factory():
        state["built"] += 1
        return backend

    factory.state = state
    return factory


def test_healthy_remote_is_selected_and_local_never_built():
    remote, local = RecordingBackend("remote"), RecordingBackend("local")
    factory = lazy(local)
    router = MemoryBackendRouter(remote, factory)
    assert router.active_backend_name == "remote"
    assert router.add("n", "lucas") == "remote:add"
    assert factory.state["built"] == 0


def test_unhealthy_remote_falls_back_to_local():
    router = MemoryBackendRouter(
        RecordingBackend("remote", healthy=False), lazy(RecordingBackend("local"))
    )
    assert router.active_backend_name == "local"
    assert router.search("q", "lucas", 5) == "local:search"


def test_no_remote_configured_uses_local():
    router = MemoryBackendRouter(None, lazy(RecordingBackend("local")))
    assert router.active_backend_name == "local"
    assert router.list_memories("lucas") == "local:list"


def test_remote_failure_mid_call_degrades_to_local_and_retries():
    remote, local = (
        RecordingBackend("remote", fail_on={"add"}),
        RecordingBackend("local"),
    )
    router = MemoryBackendRouter(remote, lazy(local))
    assert router.add("n", "lucas") == "local:add"
    assert router.active_backend_name == "local"
    assert remote.calls == [("add", ("n", "lucas"))]
    assert local.calls == [("add", ("n", "lucas"))]


def test_remote_health_probe_exception_treated_as_unhealthy():
    class Exploding(RecordingBackend):
        def is_healthy(self):
            raise RuntimeError("boom")

    router = MemoryBackendRouter(Exploding("remote"), lazy(RecordingBackend("local")))
    assert router.active_backend_name == "local"
