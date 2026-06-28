import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mem0_mcp_backend_router import MemoryBackendRouter
from mem0_mcp_local_embedded_backend import LocalEmbeddedMemoryBackend
from mem0_mcp_remote_rest_backend import RemoteRestMemoryBackend
from mem0_mcp_stdio_protocol import ModelContextProtocolStdioServer

SERVER_NAME = "mem0"
SERVER_VERSION = "1.0.0"


def build_router_from_environment():
    remote_base_url = os.environ.get("MEM0_REMOTE_BASE_URL", "").strip()
    store_directory = os.environ.get(
        "MEM0_LOCAL_STORE_DIR",
        os.path.expanduser("~/.local/share/mem0-local-fallback"),
    )
    embedding_model = os.environ.get(
        "MEM0_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    collection_name = os.environ.get("MEM0_COLLECTION_NAME", "claude_global_memory")

    remote_backend = (
        RemoteRestMemoryBackend(remote_base_url) if remote_base_url else None
    )

    def local_backend_factory():
        return LocalEmbeddedMemoryBackend(
            store_directory, embedding_model, collection_name
        )

    return MemoryBackendRouter(remote_backend, local_backend_factory)


def build_tool_definitions():
    return [
        {
            "name": "add_memory",
            "description": "Store a memory in the mem0 memory layer for later semantic recall.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The fact or note to remember.",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "Optional owner id for the memory.",
                    },
                },
                "required": ["text"],
            },
        },
        {
            "name": "search_memory",
            "description": "Semantically search stored memories for the most relevant matches.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."},
                    "user_id": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "list_memories",
            "description": "List all stored memories for the given user.",
            "inputSchema": {
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
            },
        },
        {
            "name": "delete_memory",
            "description": "Delete a single stored memory by its id.",
            "inputSchema": {
                "type": "object",
                "properties": {"memory_id": {"type": "string"}},
                "required": ["memory_id"],
            },
        },
    ]


def build_tool_handlers(router, default_user_id):
    def resolve_user_id(arguments):
        return arguments.get("user_id") or default_user_id

    def handle_add_memory(arguments):
        result = router.add(arguments["text"], resolve_user_id(arguments))
        return _serialize({"backend": router.active_backend_name, "result": result})

    def handle_search_memory(arguments):
        result = router.search(
            arguments["query"],
            resolve_user_id(arguments),
            int(arguments.get("limit", 5)),
        )
        return _serialize({"backend": router.active_backend_name, "results": result})

    def handle_list_memories(arguments):
        result = router.list_memories(resolve_user_id(arguments))
        return _serialize({"backend": router.active_backend_name, "results": result})

    def handle_delete_memory(arguments):
        result = router.delete(arguments["memory_id"])
        return _serialize({"backend": router.active_backend_name, "result": result})

    return {
        "add_memory": handle_add_memory,
        "search_memory": handle_search_memory,
        "list_memories": handle_list_memories,
        "delete_memory": handle_delete_memory,
    }


def _serialize(value):
    return json.dumps(value, default=str, ensure_ascii=False)


def main():
    default_user_id = os.environ.get("MEM0_DEFAULT_USER_ID", "lucas")
    router = build_router_from_environment()
    print(
        f"mem0-mcp: active backend at startup = {router.active_backend_name}",
        file=sys.stderr,
        flush=True,
    )
    server = ModelContextProtocolStdioServer(
        SERVER_NAME,
        SERVER_VERSION,
        build_tool_definitions(),
        build_tool_handlers(router, default_user_id),
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
