---
name: claude-code-oneshot
description: Run Claude Code as a one-shot autonomous coding session with no back-and-forth. Use when delegating complex tasks that need deep focus, large context, or long-running execution. Also use when spawning a subagent for refactoring, migration, or implementation work that is straightforward to verify.
---

<when_to_use>
Complex refactoring or feature implementation with clear success criteria. Tasks that would bloat your current context. Parallel execution across worktrees. Anything where tests or script output can verify the result.
</when_to_use>

<execution>
Run claude --print "detailed task" --dangerously-skip-permissions for one-shot mode. The --print flag runs the task and exits. Be explicit in prompts — tell it exactly what to do and what not to do. Include phrases like "No questions, just implement it" to prevent clarification requests.

For longer tasks, run in background with PTY via exec pty:true background:true and monitor with process action:log/poll.
</execution>

<parallel_worktrees>
Create worktrees for independent tasks, run Claude Code in each concurrently. Each needs a git repo to operate. Wait for all to complete, then verify results.
</parallel_worktrees>

<verification>
Always verify results — run the code, check tests, confirm it works. Clear prompts prevent ambiguity. Use isolated workspaces for risky tasks. Claude Code may generate #!/bin/bash shebangs on NixOS — fix with sed to #!/usr/bin/env bash.
</verification>
