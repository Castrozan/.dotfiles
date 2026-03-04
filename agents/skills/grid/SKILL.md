---
name: grid
description: Coordinate with sibling agents on the OpenClaw grid (jarvis, clever, golden, robson, jenny, monster, silver). Use when you need help from another agent, want to delegate a task, check on a teammate, or need a capability you don't have. Also use when the user asks you to talk to, message, ping, or coordinate with another agent. Covers sessions_send, sessions_spawn, and inter-agent communication.
---

# Grid — Inter-Agent Communication

You are part of a team of AI agents running on the same OpenClaw gateway. You can talk to your siblings, delegate tasks, and coordinate work.

## Your Team

| Agent | Role | Model | Strengths |
|-------|------|-------|-----------|
| **jarvis** | Lead assistant, JARVIS persona | claude-opus | Full-stack, system admin, voice/TTS, cron management, deep research |
| **clever** | Default agent, street-smart | claude-opus | Quick responses, general tasks, user-facing chat |
| **golden** | Specialist | claude-sonnet | Cost-effective, good for bulk tasks, coding, analysis |

> This list reflects the current NixOS grid. The work PC grid has: robson, jenny, monster, silver.

## How to Communicate

### 1. `sessions_send` — Direct message (preferred)

Synchronous back-and-forth with a sibling agent. Best for quick questions and coordination.

```
sessions_send(
  sessionKey="agent:<agent_id>:main",
  message="Your message here",
  timeoutSeconds=30
)
```

- Returns the agent's reply directly
- Up to 10 ping-pong turns per conversation
- Use `timeoutSeconds=0` for fire-and-forget

### 2. `sessions_spawn` — Delegate a task

Spawn an isolated task on a sibling agent. Best for independent work.

```
sessions_spawn(
  agentId="<agent_id>",
  task="Do this thing",
  runtime="subagent"
)
```

- Runs in an isolated session
- Agent announces completion automatically
- Good for parallel work

### 3. `openclaw agent` CLI — One-shot command (via exec tool)

```bash
openclaw agent --agent <agent_id> -m "Your message" --json
```

- Creates a fresh session each time
- Good for simple one-off requests
- Response in `.result.payloads[0].text`

## When to Delegate

- **Need a cheaper model?** → Send to golden (sonnet)
- **Need a second opinion?** → Ask a sibling to review
- **Parallel tasks?** → Spawn on multiple agents simultaneously
- **User asks to contact an agent?** → Use sessions_send to their main session
- **Long-running background work?** → sessions_spawn with a clear task description

## Rules

- Always identify yourself when messaging another agent ("Hey, it's jarvis...")
- Don't spam — if an agent times out, try once more then report to the user
- Respect that each agent has their own personality and context
- The user (Lucas) can message any agent directly — don't intercept or relay unless asked
- If you need to send a message to the user on behalf of another agent, use the message tool with your own accountId

## Troubleshooting

- **"Session send visibility is restricted"** → Gateway needs restart after config change
- **Timeout** → Agent may be busy processing another request, try again
- **"agentId is not allowed"** → Check subagents.allowAgents in config
- **Discord "Unknown Channel"** → Bots can only DM users who have messaged them first
