---
name: agent-session
description: Restart or exit the current Claude Code, Codex, or OpenCode process from inside it. Use to apply a configuration change, resume work without waiting for input, or end a finished session.
---

<how_it_finds_its_target>
Run `agent-session` in the foreground through the agent's own shell tool. The command accepts no target and Herdr
resolves only the enclosing pane from `HERDR_PANE_ID`, so an agent can control itself but not another session.
</how_it_finds_its_target>

<restart>
Run `agent-session restart` to make newly built configuration live or to carry on without waiting for input. Commit
pending changes first, because restart creates a new process and only durable on-disk state survives it. Herdr resumes
the exact recorded session in the same pane and submits the continuation prompt after the replacement agent is idle.
It refuses before shutdown when it has no exact resume record. Expect no reply from the old process: the turn resumes
after restart with the continuation prompt.
</restart>

<restart_refuses_what_it_cannot_preserve>
Restart and exit fail outside Herdr and refuse to bypass a Clawde wrapper, which owns supervised-agent lifecycle. Never
work around either boundary with manual signals or a harness's most-recent-session command.
</restart_refuses_what_it_cannot_preserve>

<exit>
Run `agent-session exit` only once every task is finished, changes are committed where that applies, and you have
summarized what you accomplished, because that summary is the last thing the human reads. It reports the harness it
found and asks Herdr to stop it while preserving the pane as an idle shell. `agent-session exit --print-target` reports
the enclosing Herdr pane without stopping it.
</exit>
