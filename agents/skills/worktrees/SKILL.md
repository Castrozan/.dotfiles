---
name: worktrees
description: Create isolated git worktrees for parallel development. Use when starting feature work that needs isolation from current workspace, working on multiple branches simultaneously, or before executing implementation plans that should not affect the main workspace.
---

<announcement>
"I'm using the worktrees skill to set up an isolated workspace."
</announcement>

<workflow>
Before creating a worktree, update main branch: `git fetch origin && git checkout main && git pull`. This ensures new branches start from the latest code.

Claude Code has built-in worktree support. Use `claude --worktree <name>` or `-w <name>` to start a session in an isolated worktree at `.claude/worktrees/<name>/`. Subagents can use `isolation: "worktree"` in their definition to run in a temporary worktree that auto-cleans if no changes are made. Avoid branch names with `/` as they create nested directories.

Before finishing your implementation use /rebuild skill to rebuild or test the rebuild in the worktree changes. If your implementation works, and you rebuilt and tested or manually tested, continue to PR creation.

Push to remote and create PR/MR with `gh` or `glab`. Run PR commands from main repo directory (not worktree) to avoid git detection issues: `cd /path/to/repo && gh pr create --head <branch> --title "..." --body "..."`. Monitor CI with `gh pr checks <number>` or `glab ci status`. Share the PR/MR link and continue with /pr-iteration for code review handling.

Maintain worktree isolation throughout the session. If worktree breaks due to deleted CWD, recreate rather than falling back to main. After PR merged or pending review, return to main workspace and rebuild from main branch so system returns to stable state. Keep worktree locally for follow-up work.
</workflow>

<red_flags>
Never skip tests before declaring ready. Never commit to main when worktree isolation was requested.
</red_flags>
