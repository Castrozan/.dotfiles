# mem0 memory MCP

Global Claude Code gets a long-term memory layer backed by a remote
[OpenMemory](https://github.com/mem0ai/mem0/tree/main/openmemory) MCP server.
There is no self-hosted stack here: `wrapper.nix` is a per-machine endpoint shim
that points Claude at a remote OpenMemory host when one is configured for the
machine, and leaves mem0 unwired otherwise.

## How it is wired

- `wrapper.nix` reads `private-config/machines/<host>/mem0-host.nix` (a bare base
  URL string, kept out of the public tree). When it exists, the host is
  remote-configured and the wrapper emits an `sse` MCP server entry at
  `<base-url>/mcp/claude/sse/<user>` that the managed injector writes into
  `~/.claude.json`.
- When no such file exists, the host is not remote-configured and mem0 is omitted
  from the MCP set entirely. There is no local fallback.

## Availability

The endpoint is a remote host that may be unreachable (off the network that
serves it). An `sse` MCP server spawns no local process, so an unreachable mem0
costs nothing locally: Claude simply exposes no mem0 tools that session and
reconnects when the host is back. mem0 is therefore functionally wired only when
the remote is reachable, at zero local cost when it is not.
