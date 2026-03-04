---
name: spawn-claude
description: Spawn a new Claude Code session in a tmux window with a task file. Use when delegating work to another agent, handing off a complex task for autonomous execution, or running a parallel Claude Code session in a visible tmux window. Also use when spawning subagents that need to work interactively with full context.
---

<handoff_pattern>
Write task instructions to a file, then invoke the script. The spawned agent starts with that file as its first prompt — no pasting, no timing tricks.

```sh
cat > /tmp/task.md << 'EOF'
Your detailed task here. Be explicit — this agent works autonomously.
EOF

scripts/spawn-claude.sh "session:window-name" /path/to/workdir /tmp/task.md
```

The spawned agent opens in the given tmux window and immediately reads the task. Omit `session:` prefix to use the current session.
</handoff_pattern>

<script_interface>
`scripts/spawn-claude.sh <target> <working-dir> <instructions-file> [--model MODEL]`

- `target`: `"session:window"` or just `"window"` (uses current tmux session)
- `working-dir`: directory the agent cds into before starting
- `instructions-file`: path to the task file the agent reads first
- `--model`: override the default claude model
</script_interface>

<writing_good_task_files>
The spawned agent has no prior context. Include everything it needs: what to build, where to look, what patterns to follow, what not to do. End with "Work autonomously." to prevent clarification requests.
</writing_good_task_files>
