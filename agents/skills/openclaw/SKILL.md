---
name: openclaw
description: OpenClaw multi-agent framework — packaging for the a2a-mcp-server (agent-to-agent over MCP) and the read-agent-chat helper script. Use when working on inter-agent communication, A2A protocol, or reading another agent's session history. For everyday openclaw CLI usage and operations, see the personal skill's openclaw chapter.
---

<scope>
This skill packages OpenClaw building blocks consumed by other modules:

- `install/default.nix` exposes `mcpServerCommand`, `mcpServerArgs`, and `installA2aMcpViaNpm` for the a2a-mcp-server. Imported explicitly by `home/modules/claude/mcps.nix` to build the streamable-http bridge.
- `scripts/read-agent-chat.sh` reads chat history from another agent's session JSONL files.

The framework itself (gateway, agents, telegram bots) is configured through `home/modules/openclaw/`, not here.
</scope>
