---
name: restart
description: Restart the current Claude Code, Codex, or OpenCode process and invoke its native resume form in the same pane. Use after a configuration change or to resume work without waiting for input.
---

<prerequisites>
Running inside herdr. Commit any pending changes before restarting.
</prerequisites>

<execution>
Run `agent-session restart`.
</execution>

<continuation>
The command uses an explicit session identifier when the running command exposes one. Otherwise it uses the harness's
native continue or most-recent-session behavior, then relaunches in the same herdr pane.
It fails safely outside herdr, because it cannot preserve the interactive session location there.
It also refuses to bypass a Clawde wrapper, which owns the harness command and session record for supervised agents.
</continuation>

<notes>
The detached launcher waits for the prior process to exit before sending the resume command. A resume still starts a new
process, so only durable on-disk state is guaranteed across it.
</notes>
