import sys

from mem0_memory_backends import RemoteUnavailable


class MemoryBackendRouter:
    def __init__(self, remote_backend, local_backend_factory):
        self.remote_backend = remote_backend
        self.local_backend_factory = local_backend_factory
        self._local_backend = None
        self.active_backend_name = self._select_primary()

    def _select_primary(self):
        if self.remote_backend is not None and self._remote_is_healthy():
            return "remote"
        return "local"

    def _remote_is_healthy(self):
        try:
            return self.remote_backend.is_healthy()
        except Exception:
            return False

    def _local(self):
        if self._local_backend is None:
            self._local_backend = self.local_backend_factory()
        return self._local_backend

    def add(self, text, user_id):
        return self._dispatch(lambda backend: backend.add(text, user_id))

    def search(self, query, user_id, limit):
        return self._dispatch(lambda backend: backend.search(query, user_id, limit))

    def list_memories(self, user_id):
        return self._dispatch(lambda backend: backend.list_memories(user_id))

    def delete(self, memory_id):
        return self._dispatch(lambda backend: backend.delete(memory_id))

    def _dispatch(self, operation):
        if self.active_backend_name == "remote":
            try:
                return operation(self.remote_backend)
            except RemoteUnavailable as failure:
                print(
                    f"mem0-mcp: remote failed mid-call, degrading to local: {failure}",
                    file=sys.stderr,
                    flush=True,
                )
                self.active_backend_name = "local"
        return operation(self._local())
