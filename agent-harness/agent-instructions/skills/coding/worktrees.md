<builtin_worktree>
Claude Code has a built-in `--worktree` flag and EnterWorktree/ExitWorktree tools for simple isolation. Use built-in
worktree for quick subagent isolation where you need a throwaway branch. Use this skill's manual workflow when you need
persistent worktrees, multiple simultaneous branches, or PR workflows from worktrees.
</builtin_worktree>

<worktree_creation>
Fetch latest main before branching. Create worktrees at `.worktrees/<branch>` inside the project directory; this path is
gitignored. Avoid branch names containing `/` as they create nested directories that break the convention. Use the Git
worktree command's help for exact syntax.
</worktree_creation>

<location_is_enforced>
A worktree never lives outside its repository, because a sibling checkout is a stray copy of the repo that outlives the
branch, nothing gitignores it, and a temp directory hands it to the OS purge and to whatever scans unexcluded paths. The
accepted destinations are `.worktrees/<branch>` and the built-in `.claude/worktrees/<name>` that `--worktree` and
EnterWorktree create; a bare name, `../<name>`, an absolute path, and anything under `/tmp` are all refused. The rule
binds you, not the tooling: the `worktree_location_guard` PreToolUse hook denies a stray `git worktree add` on the
claude harness only, so an agent on opencode or codex gets no refusal and must hold the location itself. For a genuinely
sanctioned exception prefix the command with `WORKTREE_OUTSIDE_REPOSITORY_SANCTIONED=1`. Relocate a stray worktree with
`git worktree move`, which preserves its branch and uncommitted state, except where the repo carries submodules: git
refuses to move or remove that worktree at all, so delete the directory and `git worktree prune`, first confirming its
commits are ancestors of the upstream branch and its submodules clean.
</location_is_enforced>

<traps>
PR commands must run from the main repo directory, not the worktree: `gh` and `glab` misdetect the repo context inside
worktrees. Use `--head <branch>` to target the worktree branch.

Never run `git checkout` or `git switch` in the main repo: the main repo stays on its current branch at all times. All
branch work happens exclusively inside the worktree directory. Each worktree is bound to one branch; if you need a
different branch, create a new worktree.

If the worktree CWD gets deleted mid-session, recreate the worktree rather than silently falling back to main. Never
commit to main when worktree isolation was requested; this is the most common failure mode.

After PR is merged or pending review, return to main workspace and rebuild so the system returns to stable state. Keep
the worktree locally for follow-up work during review.
</traps>
