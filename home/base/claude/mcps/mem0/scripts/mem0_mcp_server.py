import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

from mem0_backend_router import MemoryBackendRouter
from mem0_memory_backends import LocalNoLlmMemory, RemoteMemory

DEFAULT_USER_ID = os.environ.get("MEM0_DEFAULT_USER_ID", "lucas")

mcp = FastMCP("mem0")


def build_router():
    remote_base_url = os.environ.get("MEM0_REMOTE_BASE_URL", "").strip()
    store_directory = os.environ.get(
        "MEM0_LOCAL_STORE_DIR", os.path.expanduser("~/.local/share/mem0-local-fallback")
    )
    embedding_model = os.environ.get(
        "MEM0_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    collection_name = os.environ.get("MEM0_COLLECTION_NAME", "claude_global_memory")
    remote_backend = RemoteMemory(remote_base_url) if remote_base_url else None
    return MemoryBackendRouter(
        remote_backend,
        lambda: LocalNoLlmMemory(store_directory, embedding_model, collection_name),
    )


router = build_router()


def _envelope(payload):
    return json.dumps(
        {"backend": router.active_backend_name, **payload},
        default=str,
        ensure_ascii=False,
    )


@mcp.tool()
def add_memory(text: str, user_id: str = "") -> str:
    """Store a memory in the mem0 memory layer for later semantic recall."""
    return _envelope({"result": router.add(text, user_id or DEFAULT_USER_ID)})


@mcp.tool()
def search_memory(query: str, user_id: str = "", limit: int = 5) -> str:
    """Semantically search stored memories for the most relevant matches."""
    return _envelope(
        {"results": router.search(query, user_id or DEFAULT_USER_ID, limit)}
    )


@mcp.tool()
def list_memories(user_id: str = "") -> str:
    """List all stored memories for the given user."""
    return _envelope({"results": router.list_memories(user_id or DEFAULT_USER_ID)})


@mcp.tool()
def delete_memory(memory_id: str) -> str:
    """Delete a single stored memory by its id."""
    return _envelope({"result": router.delete(memory_id)})


def main():
    print(
        f"mem0-mcp: active backend at startup = {router.active_backend_name}",
        file=sys.stderr,
        flush=True,
    )
    mcp.run()


if __name__ == "__main__":
    main()
