---
name: grid
description: Coordinate with sibling agents on the OpenClaw grid (jarvis, clever, golden, robson, jenny, monster, silver). Use when you need help from another agent, want to delegate a task, check on a teammate, or need a capability you don't have. Also use when the user asks you to talk to, message, ping, or coordinate with another agent. Covers sessions_send, sessions_spawn, and inter-agent communication.
---

<team>
| Agent | Role | Model | Strengths |
|-------|------|-------|-----------|
| **jarvis** | Lead assistant, JARVIS persona | claude-opus | Full-stack, system admin, voice/TTS, cron management, deep research |
| **clever** | Default agent, street-smart | claude-opus | Quick responses, general tasks, user-facing chat |
| **golden** | Specialist | claude-sonnet | Cost-effective, good for bulk tasks, coding, analysis |

This list reflects the current NixOS grid. The work PC grid has: robson, jenny, monster, silver.
</team>

<communication_methods>
sessions_send: synchronous back-and-forth, up to 10 turns. Best for quick questions. Use timeoutSeconds=0 for fire-and-forget.
sessions_spawn: isolated task on a sibling agent. Best for parallel independent work. Agent announces completion automatically.
openclaw agent CLI: one-shot command via exec tool. Fresh session each time, good for simple requests.
</communication_methods>

<when_to_delegate>
Need a cheaper model → golden (sonnet). Need a second opinion → ask a sibling to review. Parallel tasks → spawn on multiple agents. User asks to contact an agent → sessions_send to their main session. Long-running background work → sessions_spawn with clear task description.
</when_to_delegate>

<rules>
Always identify yourself when messaging another agent. Don't spam — if an agent times out, try once more then report to the user. Respect each agent's personality and context. Don't intercept or relay user messages unless asked.
</rules>

<troubleshooting>
"Session send visibility is restricted": gateway needs restart after config change. Timeout: agent may be busy, try again. "agentId is not allowed": check subagents.allowAgents in config. Discord "Unknown Channel": bots can only DM users who have messaged them first.
</troubleshooting>
