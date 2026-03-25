<when_to_use>
Cross-vendor agent communication only. For OpenClaw agents on the same gateway, use sessions_spawn via the grid skill — faster and already configured. A2A is for agents that speak the A2A protocol over HTTP.
</when_to_use>

<workflow>
Fetch the agent card first to discover capabilities, then send messages. Tasks may be asynchronous — poll with get_task if the agent returns a task ID instead of an immediate response. The MCP tools are self-documenting; read their descriptions for parameters and return types.
</workflow>

<traps>
Agent cards live at `/.well-known/agent-card.json` on the agent's host. If the URL is wrong or the agent doesn't implement A2A, the card fetch fails silently with a 404. Some agents require authentication — check the agent card's securitySchemes before sending messages.
</traps>
