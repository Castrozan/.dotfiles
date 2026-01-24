---
name: worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<announcement>
"I'm using the worktrees skill to set up an isolated workspace."
</announcement>

<workflow>
Git worktrees create isolated workspaces sharing the same repository. Create worktrees in `.worktree/<branch>` inside the project directory using `git worktree add .worktree/<branch> -b <branch>`. For ~/.dotfiles repo use `./bin/git-worktree-crypt <branch>` instead (creates at `.worktrees/<branch>`, uses git-crypt). Avoid branch names with `/` as they create nested directories.

After worktree creation, implement changes following project rules and commit frequently at every major change. Test before proceeding: use /rebuild for ~/.dotfiles, appropriate test commands for other projects. Push to remote and create PR/MR with clear description and test results. Run PR commands from main repo directory (not worktree) to avoid git detection issues: `cd /path/to/repo && gh pr create --head <branch> --title "..." --body "..."`. Monitor CI with `gh pr checks <number>` or `glab ci status`. Share the PR/MR link and continue with /pr-iteration for code review handling.

Maintain worktree isolation throughout the session. If worktree breaks due to deleted CWD or git-crypt issues, recreate rather than falling back to main. After PR merged or pending review, return to main workspace and rebuild from main branch so system returns to stable state. Keep worktree locally for follow-up work.
</workflow>

<red_flags>
Never skip tests before declaring ready. Never commit to main when worktree isolation was requested. In ~/.dotfiles, never use plain `git worktree add`.
</red_flags>
