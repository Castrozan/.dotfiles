---
name: project-agent
description: Launch and manage persistent project agents - Claude Code sessions that run in a loop with heartbeat, maintain project state, and work autonomously. OpenClaw-style persistent agents using Claude Code.
---

Launch a persistent Claude Code session that acts as a project manager for a specific project directory. The agent runs in a tmux window, sets up heartbeat crons to work autonomously when idle, maintains state on disk, and remains fully interactive.

<launch>
Use `launch-project-agent.sh` from this skill's `scripts/` directory. It creates a tmux window, starts Claude Code pointed at the project directory, and sends a bootstrap prompt that makes the agent read its state and set up heartbeat crons.

Run `launch-project-agent.sh --help` for syntax. Minimum: a project directory that contains a CLAUDE.md.

After launch, the agent:
1. Reads the project CLAUDE.md (its identity and instructions)
2. Reads HEARTBEAT.md for pending work
3. Sets up durable heartbeat crons via CronCreate
4. Either acts on pending work or waits for user input

The user interacts by typing in the tmux window. Between interactions, the heartbeat fires and the agent checks for autonomous work.
</launch>

<project-requirements>
A project directory must have at minimum:
- `CLAUDE.md` - the agent's identity, role, instructions, and project context. This defines what the agent is and how it behaves. Without it, the agent has no purpose.
- `HEARTBEAT.md` - the heartbeat checklist. Can start empty with `# Heartbeat\n\nNo active work.`

The launch script validates both exist before starting.
</project-requirements>

<heartbeat-behavior>
For heartbeat configuration, format, and autonomous work patterns, read `heartbeat.md`.
</heartbeat-behavior>

<interaction-with-other-sessions>
The project agent runs in its own tmux window. Other Claude Code sessions (executors) can be launched in separate tmux windows for implementation work. Both can communicate:

- Agent Teams: the project agent can spawn teammates via TeamCreate
- tmux send-keys: inject prompts into other sessions' tmux panes
- Shared files: both read/write the same project files, HEARTBEAT.md, and state files

The project agent delegates work. Executor sessions do work. The project agent reviews results.
</interaction-with-other-sessions>

<persistence>
The tmux window persists independently of the spawning session. If the Claude Code process inside crashes or exits, the tmux window remains and can be restarted manually or via systemd.

For production-grade persistence (auto-restart on crash), create a systemd user service that manages the tmux session - same pattern as the Discord channel agents in `home/modules/claude/channels.nix`.

Heartbeat crons are session-scoped - they live only while the Claude Code process runs. The bootstrap prompt re-registers the heartbeat on every session start, so restarts are handled automatically by the launch script.
</persistence>

<state-files>
State files live in the project directory alongside CLAUDE.md. Convention:
- `HEARTBEAT.md` - heartbeat task checklist (agent-directed, structured)
- `sessions/YYYY-MM-DD.md` - daily work logs (agent-directed)
- Any other state files the project CLAUDE.md defines

All state files are agent-directed content. Human-directed content follows the project's own conventions (e.g., README.md).
</state-files>
