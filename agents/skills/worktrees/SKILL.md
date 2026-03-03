---
name: worktrees
description: Create isolated git worktrees for parallel development. Use when starting feature work that needs isolation from current workspace, working on multiple branches simultaneously, or before executing implementation plans that should not affect the main workspace.
---

<announcement>
"I'm using the worktrees skill to set up an isolated workspace."
</announcement>

<worktree_creation>
Before creating a worktree, update main branch: `git fetch origin && git checkout main && git pull`. This ensures new branches start from the latest code. Avoid branch names with `/` as they create nested directories.

```bash
git worktree add .worktrees/<branch-name> -b <branch-name>
```

Worktrees live at `.worktrees/<branch>` inside the project directory and are gitignored.
</worktree_creation>

<development_workflow>
After worktree creation:

1. Implement changes in the isolated workspace following project conventions
2. Commit frequently — multiple small commits beat one giant commit
3. Test with /rebuild skill (dotfiles) or project-appropriate test commands
4. Push to remote and create PR/MR
5. Monitor CI, share link, iterate with /pr-iteration skill
6. After PR merged or pending review, return to main workspace and rebuild from main so system returns to stable state
</development_workflow>

<pr_creation>
Run PR commands from the main repo directory (not the worktree) to avoid git detection issues:
```bash
cd /path/to/repo && gh pr create --head <branch> --title "..." --body "..."
```
Monitor CI with `gh pr checks <number>` or `glab ci status`.
</pr_creation>

<session_persistence>
Maintain worktree isolation throughout the session. If worktree breaks due to deleted CWD, recreate rather than falling back to main. Never commit to main when worktree isolation was requested. Keep worktree locally for follow-up work after PR is pending review.
</session_persistence>

<red_flags>
Never skip tests before declaring ready. Never commit to main when worktree isolation was requested. Never create worktrees in directories that are not gitignored. Avoid branch names with `/` as they create nested directories.
</red_flags>
