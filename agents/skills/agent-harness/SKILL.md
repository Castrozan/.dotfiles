---
name: agent-harness
description: Debug and configure the Claude Code, Codex, or OpenCode harness instead of the project it edits. Use for settings, skills, hooks, model routing, transcripts, MCPs, session state, or tool-targeting failures.
---

<scope>
Treat the harness as runtime infrastructure, not application code. Use this when a setting, skill, hook, connector,
subagent, model, transcript, session, or tool target behaves differently from the configured source.
</scope>

<live-state-over-files>
Read the declared source, then inspect the running harness, process, and session. A deployed file does not prove a
harness loaded it, and a resumed session can retain state from before a rebuild. Compare versions and live state before
calling a documented behavior a defect.
</live-state-over-files>

<configuration-ownership>
Keep durable settings and instruction surfaces declarative. Preserve harness-owned mutable state where the deployment
model requires it, and restart a session only after its replacement is available. Use `agent-session` for a generic
restart or exit instead of assuming a Claude-specific command.
</configuration-ownership>

<knowledge>
Read `knowledge.md` for harness-specific traps, including transcript locations, configuration roots, model routing,
hook protocols, skill discovery, connector gates, and command anchoring.
</knowledge>
