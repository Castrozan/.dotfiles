---
name: herdr
description: Drive herdr, the terminal workspace manager, and orchestrate Claude Code agents in it: spawn, prompt, read, wait on, or take over a background Claude. Also scripts herdr workspaces, tabs, and panes.
---

<orientation>
herdr is the primary multiplexer on every host; tmux is retired. Its CLI is self-documenting, so run `herdr <noun> --help` for exact flags rather than memorizing them: nouns are `workspace`, `tab`, `pane`, `agent`, and `wait`. They nest - a workspace holds tabs, a tab holds panes, and an agent is a claude or codex process reported against a pane. Every command talks to the running server over its own socket automatically, so unlike tmux there is no socket path to detect and no "no server running" trap to work around.
</orientation>

<orchestrating_agents>
Spawn a Claude with `herdr agent start <name> --cwd <dir> --tab "$HERDR_TAB_ID" --no-focus [--split right|down] -- claude [--model M] [--name N]`; everything after `--` is the launched argv. Pin placement to your own `$HERDR_TAB_ID` and pass `--no-focus`: an unpinned `agent start` splits the focused pane into whatever window the user switched to, and a guard blocks it (target elsewhere only with an explicit `--workspace`/`--tab`). Synchronize on reported state, not scraped output: `herdr agent wait <target> --status idle|working|blocked [--timeout MS]` blocks until the agent reaches that state, so wait for `idle` before the first prompt and after every turn instead of polling `agent read`. Read output with `herdr agent read <target> [--source visible|recent|recent-unwrapped] [--lines N]`. A target is the agent name, a terminal id, or a pane id.
</orchestrating_agents>

<prompt_submission_trap>
`herdr agent send <target> <text>` writes literal text and does not press Enter, so a prompt sits unsubmitted until you send Enter separately with `herdr pane send-keys <pane> Enter`; `pane run` appends Enter but is for shell command lines, not prompt prose. Never send a multi-line prompt as-is: each embedded newline submits mid-thought. Write a task to a file and send a one-line `read <file> and implement it` so nothing submits early.
</prompt_submission_trap>

<when_to_spawn>
Spawn a herdr agent when the user must watch or take over the work, when it needs a persistent interactive session, or when it must outlive this conversation. For read-only research, exploration, or search, use the builtin Agent tool with no herdr. For multi-agent work that edits code, run a Workflow (see the `deliver` skill) with worktree isolation, never Teams.
</when_to_spawn>

<resume_and_liveness>
Continue a spawned agent later with `claude --resume <id>` in a fresh agent pane; the id is in claude's status bar and is the name of its transcript jsonl. When a spawned agent's claude exits, its pane survives as an idle shell rather than closing, so a later reference focuses a dead pane; detect liveness by process, not presence - a pane is idle when its `foreground_process_group_id` equals its `shell_pid` in `herdr pane process-info`, and relaunch into it instead of assuming the agent is alive.
</resume_and_liveness>

<oneshot_is_gated>
Headless `claude --print` is blocked by a guard because interactive herdr agents are the sanctioned path; for a genuinely sanctioned one-off, prefix the command with `CLAUDE_HEADLESS_SANCTIONED=1`.
</oneshot_is_gated>
