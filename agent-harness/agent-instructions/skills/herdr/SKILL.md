---
name: herdr
description: Drive herdr, the terminal workspace manager, and orchestrate interactive agents in it: spawn, prompt, read, wait on, or take over background work. Also scripts workspaces, tabs, and panes.
---

<orientation>
herdr is the primary multiplexer on every host; tmux is retired. Its CLI is self-documenting, so run `herdr <noun>
--help` for exact flags rather than memorizing them: nouns are `workspace`, `tab`, `pane`, `agent`, and `wait`. They
nest - a workspace holds tabs, a tab holds panes, and an agent is a harness process reported against a pane. Every
command talks to the running server over its own socket automatically, so unlike tmux there is no socket path to detect
and no "no server running" trap to work around.
</orientation>

<orchestrating_agents>
Launch a supported harness into the pane a new tab already carries, so the agent is born alone in one pane: `herdr tab
create --workspace "$HERDR_WORKSPACE_ID" --cwd <dir> --no-focus` answers with that tab and its root pane id, and `herdr
pane run <root pane id> <harness> <arguments>` starts the harness there. Carry the working directory and any
environment on the create, because `pane run` takes neither. Pin the workspace and pass `--no-focus` so creation
neither lands in nor moves the view to whatever the human switched to. Never reach for `herdr agent start`: it always
splits a tab and never opens one, so even pinned to a fresh tab it strands that tab's root shell beside the agent with
no close verb able to clear it, and a guard blocks its unpinned form, which splits the tab the human switched to.
`pane run` starts no named agent, so name it afterwards with `herdr agent rename <pane id> <name>`; until then the pane
id is the only target that resolves, because `agent list` does not carry the pane the instant `pane run` returns.
Synchronize on reported state, not scraped output: `herdr agent wait <target> --status idle|working|blocked [--timeout
MS]` blocks until the agent reaches that state and takes a pane id before detection lands, so wait for `idle` to cover
the harness boot before the first prompt and after every turn instead of polling `agent read`. Read output with `herdr
agent read <target> [--source visible|recent|recent-unwrapped] [--lines N]`. A target is the agent name, a terminal id,
or a pane id.
</orchestrating_agents>

<prompt_submission_trap>
`herdr agent send <target> <text>` writes literal text and does not press Enter, so a prompt sits unsubmitted until you
send Enter separately with `herdr pane send-keys <pane> Enter`; `pane run` appends Enter but is for shell command lines,
not prompt prose. Never send a multi-line prompt as-is: each embedded newline submits mid-thought. Write a task to a
file and send a one-line `read <file> and implement it` so nothing submits early.
</prompt_submission_trap>

<when_to_spawn>
Spawn a herdr agent when the user must watch or take over the work, when it needs a persistent interactive session, or
when it must outlive this conversation. For read-only research, exploration, or search, use the builtin Agent tool with
no herdr. Once a session is up, driving it to a goal, here or on another machine or harness, belongs to the
`orchestrate` skill. For multi-agent work that edits code, run a Workflow (see the `deliver` skill) with worktree
isolation, never Teams.
</when_to_spawn>

<resume_and_liveness>
Restart a current supported session with `agent-session restart`, which detects its harness and preserves the pane. When
a spawned agent exits, its pane survives as an idle shell rather than closing, so a later reference focuses a dead pane;
detect liveness by process, not presence. A pane is idle when its `foreground_process_group_id` equals its `shell_pid`
in `herdr pane process-info`; relaunch into it instead of assuming the agent is alive.
</resume_and_liveness>

<oneshot_is_gated>
Headless `claude --print` is blocked by a guard because interactive herdr agents are the sanctioned path; for a
genuinely sanctioned one-off, prefix the command with `CLAUDE_HEADLESS_SANCTIONED=1`.
</oneshot_is_gated>

<closing_is_gated>
Every `herdr workspace|tab|pane close` is blocked by a guard with no override, because no close proves it owns its
target and it takes every agent inside with no undo. Leave what you spawned in place and name it for the human to close.
</closing_is_gated>

<knowledge>
For traps that cost real debugging: the per-client view fork, why a CLI focus call hijacks the human's view, the
destructive shifted-digit chords, the pane-run paste wedge, and native agent resume; read `knowledge.md`. Read the
chord entry before typing any chord into a pane you do not own.
</knowledge>
