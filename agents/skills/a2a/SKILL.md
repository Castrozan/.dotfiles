---
name: a2a
description: Communicate with external A2A (Agent-to-Agent) protocol agents. Use when needing to discover, register, message, or coordinate with A2A-compatible agents outside the OpenClaw grid — Codex agents, Gemini agents, or any A2A v1.0 server.
---

<protocol>
A2A (Agent2Agent) is the open standard for inter-agent communication. Google-created, v1.0.0, HTTP + JSON-RPC 2.0 + SSE streaming. Under the Linux Foundation. The a2a-mcp-server bridge exposes A2A as MCP tools.
</protocol>

<available_tools>
These MCP tools are available when the a2a MCP server is connected:

register_agent: Register an A2A agent by URL. Fetches its Agent Card (capabilities, skills, auth). Must register before sending messages.
  Example: register_agent(url="http://localhost:41242")

list_agents: Show all registered A2A agents and their capabilities.

send_message: Send a message to a registered A2A agent. Returns a task_id for tracking.
  Example: send_message(agentId="my-agent", message="Analyze this data")

send_message_stream: Same as send_message but with real-time streaming response.

get_task_result: Retrieve the result of a previously sent message by task_id.
  Example: get_task_result(taskId="abc-123")

cancel_task: Cancel a running task on an A2A agent.

unregister_agent: Remove an A2A agent from the registry.
</available_tools>

<workflow>
1. Register the agent: provide its URL, the bridge fetches the Agent Card
2. Send a message: the bridge translates MCP → A2A JSON-RPC, returns task_id
3. Get result: poll with get_task_result or use send_message_stream for real-time

Task results persist in task_agent_mapping.json across sessions.
</workflow>

<when_to_use>
Use A2A for cross-vendor agent communication — talking to agents outside the OpenClaw grid. For OpenClaw agents on the same gateway, use sessions_spawn (grid skill) instead — it's faster and already configured.

A2A is best for: external coding agents (Codex, Gemini CLI), third-party A2A servers, cross-machine agent coordination where OpenClaw mesh is not available.
</when_to_use>

<troubleshooting>
"No agents registered": run register_agent first with the agent's URL.
Connection refused: agent server not running or wrong URL.
Auth required: some A2A agents need API keys — check the Agent Card's securitySchemes.
Timeout: A2A tasks can be long-running — use get_task_result to poll.
</troubleshooting>
