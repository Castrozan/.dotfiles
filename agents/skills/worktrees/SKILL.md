---
name: worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<announcement>
"I'm using the worktrees skill to set up an isolated workspace."
</announcement>

<core_principle>
Git worktrees create isolated workspaces sharing the same repository. Systematic directory selection combined with safety verification ensures reliable isolation.
</core_principle>

<development_workflow>
After worktree creation, write code in the isolated workspace and commit frequently to track progress. Run the rebuild script if available, otherwise do a dry build to verify changes compile. Test using appropriate methods before proceeding. Push and create a PR with clear description and test results. Keep the worktree locally for follow-up work after code review, then return to main workspace and rebuild from main branch so the system returns to stable state while PR is pending.
</development_workflow>

<session_persistence>
Maintain worktree isolation throughout the session. If the worktree breaks due to deleted CWD or git-crypt issues, recreate it rather than silently falling back to main. Never commit to main when user requested worktree isolation.
</session_persistence>

<dotfiles_worktrees>
In ~/.dotfiles repo (uses git-crypt): use `./bin/git-worktree-crypt <branch>` instead of plain `git worktree add`. Creates worktree at `.worktrees/<branch>`.
</dotfiles_worktrees>

<integration>
Called by brainstorming (Phase 4) and any skill needing isolation. Pairs with finishing-a-development-branch for cleanup, and executing-plans or subagent-driven-development where the actual work happens.
</integration>

<red_flags>
Never create worktrees in project directories. Never skip tests before declaring ready. In ~/.dotfiles, never use plain `git worktree add` - use `./bin/git-worktree-crypt`.
</red_flags>
