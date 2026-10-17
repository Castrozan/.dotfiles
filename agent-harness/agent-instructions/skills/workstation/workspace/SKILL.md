---
name: workspace
description: Switch the Bash working directory to another repo or directory for the session. Use when work must run commands outside the primary repo.
---

### Mechanism

Write an absolute path to `${XDG_STATE_HOME:-$HOME/.local/state}/agent-hooks/workspace-cwd` to switch. Create its parent
directory with mode 0700 first. A PreToolUse hook prepends `cd <dir> && direnv export` to every Bash command. Delete the
file to return to the original directory. Verify with `pwd` after switching.

### File operations trap

The hook only affects Bash. Read, Edit, Write, Glob, and Grep resolve relative paths from the original session directory
regardless of workspace state. Always use absolute paths for these tools when working in a switched workspace.

### Cleanup trap

The state file persists across sessions and survives restarts. Always delete the workspace state file when done with the
alternate workspace: leaving it active silently redirects all future Bash commands in any session.
