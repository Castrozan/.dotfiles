---
name: claude
description: Delegate work to Claude Code as an interactive session or a one-shot autonomous task. Use when spawning agents, handing off complex implementation, or running parallel coding sessions.
---

<interactive_session>
Opens a visible tmux window. Agent runs interactively — you can watch it work, intervene, or follow up. Use when you need visibility or may need to course-correct mid-task.

Invoke the spawn script from this skill's `scripts/` directory:
`spawn-claude.sh <target> <working-dir> <instructions-file> [--model MODEL]`

- `target`: `"session:window"` or just `"window"` (uses current tmux session)
- `working-dir`: directory the agent starts in
- `instructions-file`: task file the agent reads as its first prompt
</interactive_session>

<one_shot>
Runs `claude --print "task" --dangerously-skip-permissions` and exits. No window, no back-and-forth — fire and verify. Use for context-heavy refactors, parallel worktrees, or tasks with clear success criteria verifiable by tests or script output.
</one_shot>

<writing_good_task_files>
Spawned agents have no prior context. Include everything needed: what to build, where to look, what patterns to follow, what not to do. End with "Work autonomously." to prevent clarification requests.
</writing_good_task_files>
