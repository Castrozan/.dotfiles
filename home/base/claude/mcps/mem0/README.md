# mem0 memory MCP

Global Claude Code gets a long-term memory layer backed by the **official,
free, self-hosted [OpenMemory](https://github.com/mem0ai/mem0/tree/main/openmemory)
MCP server** (the mem0 project's own server). There is no custom memory server
here: `wrapper.nix` is a per-machine endpoint shim and the rest is the official
server plus its self-host config.

## How it is wired

- `wrapper.nix` picks the per-machine MCP endpoint and emits an `sse` MCP server
  entry that the managed injector writes into `~/.claude.json`:
  - on a host with `private-config/machines/<host>/mem0-host.nix` (kira) it
    points at that remote OpenMemory host, kept out of the public tree;
  - on every other host it points at the local self-hosted instance,
    `http://localhost:8765/mcp/claude/sse/<user>`.
- `openmemory-compose.yaml` self-hosts the official stack (qdrant + the
  `mem0/openmemory-mcp` image). `scripts/mem0-openmemory-up` brings it up.

## Run the local server

```bash
mem0-openmemory-up
```

It starts the stack, applies a fully local config, and creates the qdrant
collection. Proven end to end through the MCP SSE endpoint: `add_memories`
then `search_memory` recall.

## Compromises (vs the earlier custom no-LLM server), per Lucas's call

- OpenMemory needs an embedder **and** an LLM. It is configured fully local on
  **ollama** (`nomic-embed-text` embedder + `qwen2.5:3b` LLM), so no paid OpenAI
  key is required, but the strict no-LLM-local purity of the previous custom
  build is dropped.
- It needs **Docker** (Docker Desktop on darwin) and pulls two ollama models.
- OpenMemory hardcodes an OpenAI client for category tagging and creates its
  qdrant collection at OpenAI's 1536 dims. The compose routes that client to
  ollama's OpenAI-compatible endpoint, and `mem0-openmemory-up` applies the
  ollama config and creates the collection at the embedder's 768 dims.
- OpenMemory is in maintenance/sunset upstream, but it is the only free,
  self-hostable official mem0 MCP server: the official `mem0-mcp-server` targets
  the paid cloud, and the mem0 self-hosted server is REST, not MCP.
