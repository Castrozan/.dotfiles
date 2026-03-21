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
sessions_spawn (PREFERRED): isolated task on a sibling agent. Reliable, tested, works across all agents. Agent announces completion automatically. Use runtime='subagent'. One-shot tasks only (mode='run' is default). Best for parallel independent work.

openclaw agent CLI: one-shot command via exec tool. `openclaw agent --agent <id> --message "task" --json`. Fresh session each time, good for simple requests. Returns structured JSON with result.

sessions_send: synchronous back-and-forth, up to 10 turns. KNOWN BUG in OpenClaw 2026.3.13 — returns "Agent-to-agent messaging denied" even with correct allow config. Use sessions_spawn instead until fixed.
</communication_methods>

<session_keys>
Session key format for sessions_send: `agent:<agentId>:main`
Session key for spawned subagents: `agent:<agentId>:subagent:<uuid>`
Spawned subagent sessions are cleaned up after completion (mode=run).
Persistent sessions (mode=session) require thread-capable channel (Discord/Telegram).
</session_keys>

<when_to_delegate>
Need a cheaper model → golden (sonnet). Need a second opinion → ask a sibling to review. Parallel tasks → spawn on multiple agents. Long-running background work → sessions_spawn with clear task description. Simple one-shot → openclaw agent CLI.
</when_to_delegate>

<rules>
Always identify yourself when messaging another agent. Don't spam — if an agent times out, try once more then report to the user. Respect each agent's personality and context. Don't intercept or relay user messages unless asked.
</rules>

<troubleshooting>
"Agent-to-agent messaging denied by tools.agentToAgent.allow": known bug in 2026.3.13, sessions_send broken. Use sessions_spawn instead.
"Session send visibility is restricted": gateway needs restart after config change.
Timeout: agent may be busy, try again.
"agentId is not allowed": check subagents.allowAgents in config.
Model failure on spawn (0 tokens): check defaults.subagents.model — must point to a valid model with active credentials.
Discord "Unknown Channel": bots can only DM users who have messaged them first.
</troubleshooting>
