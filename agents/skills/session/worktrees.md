<announcement>
"I'm using the worktrees skill to set up an isolated workspace."
</announcement>

<builtin_worktree>
Claude Code has a built-in `--worktree` flag and EnterWorktree/ExitWorktree tools for simple isolation. Use built-in worktree for quick subagent isolation where you need a throwaway branch. Use this skill's manual workflow when you need persistent worktrees, multiple simultaneous branches, or PR workflows from worktrees.
</builtin_worktree>

<worktree_creation>
Fetch latest main before branching. Create worktrees at `.worktrees/<branch>` inside the project directory — this path is gitignored. Avoid branch names containing `/` as they create nested directories that break the convention.

```bash
git worktree add .worktrees/<branch-name> -b <branch-name>
```
</worktree_creation>

<traps>
PR commands must run from the main repo directory, not the worktree — `gh` and `glab` misdetect the repo context inside worktrees. Use `--head <branch>` to target the worktree branch.

Never run `git checkout` or `git switch` in the main repo — the main repo stays on its current branch at all times. All branch work happens exclusively inside the worktree directory. Each worktree is bound to one branch; if you need a different branch, create a new worktree.

If the worktree CWD gets deleted mid-session, recreate the worktree rather than silently falling back to main. Never commit to main when worktree isolation was requested — this is the most common failure mode.

After PR is merged or pending review, return to main workspace and rebuild so the system returns to stable state. Keep the worktree locally for follow-up work during review.
</traps>
