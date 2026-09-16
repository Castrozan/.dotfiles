---
name: herdr
description: Operate herdr workspaces, tabs, panes, processes, and persistent interactive agent sessions. Use for layout, process control, inspection, input, waiting, and takeover.
---

### Orientation

herdr is the primary multiplexer on every host; tmux is retired. Its CLI is self-documenting, so run `herdr <noun>
--help` for exact flags rather than memorizing them: nouns are `workspace`, `tab`, `pane`, `agent`, and `wait`. They
nest - a workspace holds tabs, a tab holds panes, and an agent is a harness process reported against a pane. Every
command talks to the running server over its own socket automatically, so unlike tmux there is no socket path to detect
and no "no server running" trap to work around.

### Placing work

Put work unrelated to the current goal in a new tab: `herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd <dir>
--no-focus` answers with the tab and its root pane id, and `herdr pane run <root pane id> <command>` starts the work
there. Carry the working directory and any environment on the create, because `pane run` takes neither. Keep work for
the current goal in panes of the existing tab. Before delegating any part of that goal to another agent or harness, load
`orchestrate`; it owns the pinned same-tab launch and drive loop.

### Agent observation

`pane run` starts no named agent, so name one afterwards with `herdr agent rename <pane id> <name>`; until then the pane
id is the only target that resolves, because `agent list` does not carry the pane the instant `pane run` returns.

Synchronize on reported state, not scraped output: `herdr agent wait <target> --status idle|working|blocked [--timeout
MS]` blocks until the agent reaches that state and takes a pane id before detection lands, so wait for `idle` to cover
the harness boot before the first prompt and after every turn instead of polling `agent read`.

Read output with `herdr agent read <target> [--source visible|recent|recent-unwrapped] [--lines N]`. A target is the
agent name, a terminal id, or a pane id.

### Prompt submission trap

`herdr agent send <target> <text>` writes literal text and does not press Enter, so a prompt sits unsubmitted until you
send Enter separately with `herdr pane send-keys <pane> Enter`; `pane run` appends Enter but is for shell command lines,
not prompt prose. Never send a multi-line prompt as-is: each embedded newline submits mid-thought. Write a task to a
file and send a one-line `read <file> and implement it` so nothing submits early.

### When to spawn

Spawn a herdr agent when the user must watch or take over the work, when it needs a persistent interactive session, or
when it must outlive this conversation. For read-only research, exploration, or search, use the builtin Agent tool with
no herdr. Before dispatching concurrent code editors, including native subagents, load the coding [worktree
procedure](../../development/coding/references/worktrees.md) and give each editor its own worktree; non-overlapping file
assignments do not isolate the shared Git index. Delegating part of the current goal to another agent and driving it,
here or on another machine or harness, belongs to the `orchestrate` skill.

### Resume and liveness

Restart the current supported session with `agent-session restart`; Herdr resumes its exact recorded conversation in the
same pane. When a spawned agent exits, its pane survives as an idle shell rather than closing, so a later reference
focuses a dead pane; detect liveness by process, not presence. A pane is idle when its `foreground_process_group_id`
equals its `shell_pid` in `herdr pane process-info`; relaunch into it instead of assuming the agent is alive.

### Oneshot is gated

Headless `claude --print` is blocked by a guard because interactive herdr agents are the sanctioned path; for a
genuinely sanctioned one-off, prefix the command with `CLAUDE_HEADLESS_SANCTIONED=1`.

### Owned pane cleanup

Close every pane or tab you create when its work finishes. Keep it only when the user explicitly asks to preserve or
take over that session, and never close a pre-existing pane. A close carries a literal target id or a guard blocks it:
`herdr workspace|tab|pane close <id>` is yours to run, a bare verb or a `$VAR` the guard cannot resolve is not. Ids are
stable and are not reused after a close, but a close takes every agent inside with no undo. Re-list and match your own
label immediately before closing to prove that the target still exists and remains yours.

### Knowledge

For traps that cost real debugging: per-client view isolation, why a CLI focus call hijacks the human's view, stable
structural ids versus rotating terminal ids, destructive shifted-digit chords, the pane-run paste wedge, and native
agent resume; read [knowledge](references/knowledge.md). Read the chord entry before typing any chord into a pane you do
not own.
