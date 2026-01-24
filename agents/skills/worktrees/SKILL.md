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

<worktree_location>
Create worktrees in `.worktree/<branch>` inside the project directory. This keeps worktrees local to each project and easy to find.

For ~/.dotfiles repo specifically: use `./bin/git-worktree-crypt <branch>` which creates at `.worktrees/<branch>` (note the 's' - this script predates the convention).

For other projects:
```bash
git worktree add .worktree/<branch-name> -b <branch-name>
```
</worktree_location>

<development_workflow>
After worktree creation:

1. **Implement**: Write code in the isolated workspace following project rules and git best practices
2. **Commit frequently**: Commit at every major change to track progress (multiple small commits beat one giant commit)
3. **Test**:
   - For ~/.dotfiles: use /rebuild skill to verify changes
   - For other projects: run appropriate test commands (test suite, linter, build)
4. **Push and create PR/MR**: Push to remote, create PR (GitHub) or MR (GitLab) with clear description and test results
5. **Monitor CI**: Check that CI pipeline passes
6. **Share link**: Provide the PR/MR URL to user
7. **Iterate**: Use /pr-iteration skill for code review handling
8. **Return to main**: Go back to main workspace and rebuild from main branch so system returns to stable state while PR is pending
</development_workflow>

<session_persistence>
Maintain worktree isolation throughout the session. If the worktree breaks due to deleted CWD or git-crypt issues, recreate it rather than silently falling back to main. Never commit to main when user requested worktree isolation.
</session_persistence>

<pr_workflow>
After implementation and testing pass:
- GitHub: `gh pr create --title "..." --body "..."`
- GitLab: `glab mr create --title "..." --description "..."`

Monitor CI with:
- GitHub: `gh pr checks <number>`
- GitLab: `glab ci status`

After PR/MR created, answer with the link and continue with /pr-iteration skill for handling reviews.
</pr_workflow>

<integration>
Called by brainstorming (Phase 4) and any skill needing isolation. Pairs with /rebuild for testing, /commit for frequent commits, /pr-iteration for code review handling.
</integration>

<red_flags>
Never skip tests before declaring ready. Never commit to main when worktree isolation was requested. In ~/.dotfiles, never use plain `git worktree add` - use `./bin/git-worktree-crypt`. Avoid branch names with `/` as they create nested directories.
</red_flags>
