---
name: worktrees
description: Create isolated git worktrees for parallel development. Use when starting feature work that needs isolation from current workspace, working on multiple branches simultaneously, or before executing implementation plans that should not affect the main workspace.
---

<announcement>
"I'm using the worktrees skill to set up an isolated workspace."
</announcement>

<worktree_creation>
Fetch latest main before branching. Create worktrees at `.worktrees/<branch>` inside the project directory — this path is gitignored. Avoid branch names containing `/` as they create nested directories that break the convention.

```bash
git worktree add .worktrees/<branch-name> -b <branch-name>
```
</worktree_creation>

<traps>
PR commands must run from the main repo directory, not the worktree — `gh` and `glab` misdetect the repo context inside worktrees. Use `--head <branch>` to target the worktree branch.

If the worktree CWD gets deleted mid-session, recreate the worktree rather than silently falling back to main. Never commit to main when worktree isolation was requested — this is the most common failure mode.

After PR is merged or pending review, return to main workspace and rebuild so the system returns to stable state. Keep the worktree locally for follow-up work during review.
</traps>
