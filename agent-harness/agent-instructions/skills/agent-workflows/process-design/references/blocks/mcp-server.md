---
block: mcp-server
group: hands
provides: action, observable
needs: driver
---

### What it gives

The process's tools exposed through the Model Context Protocol, so every harness and every peer calls the same actions.

### Use when

Several harnesses or peers need the same actions, or a tool needs a typed schema and its own permission boundary. Avoid
it for one script one agent calls.

### Instruction

Expose each action with a narrow schema and least privilege. Keep destructive actions behind the same gates the script
enforces.

### Harness

Any MCP-capable harness; Claude Code, Codex, and OpenCode all connect to MCP servers.
