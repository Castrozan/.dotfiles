# A worktree was placed outside the repository

A worktree outside the repo is a stray copy of it on the filesystem that
nothing ignores or cleans up. Inside the repo, the ignore rules already cover
it.

Create it under `.worktrees/<branch>`:

    git worktree add .worktrees/<branch> -b <branch>

The built-in `.claude/worktrees/` path is accepted too, so an agent that makes
its own isolated worktree is not fighting this guard.

For a genuinely sanctioned exception, prefix the command with
`WORKTREE_OUTSIDE_REPOSITORY_SANCTIONED=1`.
