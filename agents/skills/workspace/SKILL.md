---
name: workspace
description: Switch working directory mid-session to work in different project workspaces. Loads direnv environments, venvs, and project-local tools. Use when needing to run project-local commands (npm, uv, cargo, make) in a directory other than where Claude was launched.
---

<mechanism>
Write an absolute path to `/tmp/claude-code-workspace-cwd` to switch. A PreToolUse hook prepends `cd <dir> && direnv export` to every Bash command. Delete the file to return to the original directory. Verify with `pwd` after switching.
</mechanism>

<file_operations_trap>
The hook only affects Bash. Read, Edit, Write, Glob, and Grep resolve relative paths from the original session directory regardless of workspace state. Always use absolute paths for these tools when working in a switched workspace.
</file_operations_trap>

<cleanup_trap>
The state file persists across sessions and survives restarts. Always delete `/tmp/claude-code-workspace-cwd` when done with the alternate workspace — leaving it active silently redirects all future Bash commands in any session.
</cleanup_trap>
