---
block: mcp-server
group: hands
provides: action, observable
needs: driver
---

# mcp-server

### What it gives

The process's tools, resources, and prompts exposed through the Model Context Protocol, so every harness and every peer
calls the same actions.

### Use when

Several harnesses or peers need the same actions, or a tool needs a stateful connection, authentication, or server-side
data. Prefer a command-line tool when one exists, since it costs less context, and avoid loading many servers' tools
upfront.

### Instruction

Give each tool one distinct purpose, a clear description with examples, and parameters that prevent mistakes, such as
absolute paths. Present a large tool surface as a code API the agent filters in code, keep the tool set stable during a
task, and keep destructive tools behind the same gates the script enforces.

### Pitfalls

Tool descriptions from untrusted servers are untrusted input; supply-chain risk; context bloat from tool definitions.

### Harness

Claude Code, Codex, and OpenCode all connect to MCP servers, and Claude Code can scope servers per subagent; Camunda can
expose a process as an MCP tool.
