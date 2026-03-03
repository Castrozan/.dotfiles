---
name: worktrees
description: Create isolated git worktrees for parallel development. Use when starting feature work that needs isolation from current workspace, working on multiple branches simultaneously, or before executing implementation plans that should not affect the main workspace.
---

<announcement>
"I'm using the worktrees skill to set up an isolated workspace."
</announcement>

<worktree_creation>
Before creating a worktree, update main branch: `git fetch origin && git checkout main && git pull`. This ensures new branches start from the latest code. Avoid branch names with `/` as they create nested directories.

For git-crypt repositories like ~/.dotfiles, use the dedicated script:
```bash
./bin/git-worktree-crypt <branch-name>
```
This handles disabling git-crypt filters during checkout and symlinking encryption keys into the worktree. Never use plain `git worktree add` in git-crypt repos — it will fail with smudge filter errors.

For standard repositories:
```bash
git worktree add .worktrees/<branch> -b <branch>
```
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
Maintain worktree isolation throughout the session. If worktree breaks due to deleted CWD or git-crypt issues, recreate rather than falling back to main. Never commit to main when worktree isolation was requested.
</session_persistence>

<red_flags>
Never skip tests before declaring ready. Never commit to main when worktree isolation was requested. In git-crypt repos like ~/.dotfiles, never use plain `git worktree add` — use `./bin/git-worktree-crypt`. Never create worktrees in directories that are not gitignored. Avoid branch names with `/` as they create nested directories.
</red_flags>
