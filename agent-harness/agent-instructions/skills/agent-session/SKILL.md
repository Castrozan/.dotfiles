---
name: agent-session
description: Restart or exit the current Claude Code, Codex, or OpenCode process from inside it. Use to apply a configuration change, resume work without waiting for input, or end a finished session.
---

<how_it_finds_its_target>
Every subcommand walks the calling process's own ancestry for a supported harness, so run `agent-session` in the
foreground through the harness's own shell tool; a detached, backgrounded, or separately launched invocation finds no
harness ancestor and refuses instead of acting on some other process.
</how_it_finds_its_target>

<restart>
Run `agent-session restart` to make newly built configuration live or to carry on without waiting for input. Commit
pending changes first, because a resume starts a new process and only durable on-disk state survives it. The command
terminates the harness and a detached launcher resumes the same session in the same herdr pane, using an explicit
session identifier from the harness or the pane's reported session. It refuses before termination when neither exposes
an exact identifier; never replace that preservation boundary with a harness's global continue or most-recent-session
form. Expect no reply: this session ends mid-command and returns as a resumed one holding a continuation prompt.
</restart>

<restart_refuses_what_it_cannot_preserve>
Restart fails outside herdr, where it cannot preserve the interactive session location, and refuses to bypass a Clawde
wrapper, which owns the harness command and session record for supervised agents. Read either refusal as a boundary
rather than as a reason to kill and relaunch the harness by hand.
</restart_refuses_what_it_cannot_preserve>

<exit>
Run `agent-session exit` only once every task is finished, changes are committed where that applies, and you have
summarized what you accomplished, because that summary is the last thing the human reads. It reports the harness it
found and terminates it together with its direct children, and `--print-target` names that target without killing
anything. When it finds no target, use the harness's own exit control rather than signaling an unrelated process.
</exit>

<launch>
`agent-session launch` is the detached relaunch step that `restart` spawns for itself, never a command to invoke: on its
own it types a resume command into a pane whose harness is still running.
</launch>
