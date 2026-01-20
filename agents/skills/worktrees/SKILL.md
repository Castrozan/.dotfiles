---
name: worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<announcement>
"I'm using the worktrees skill to set up an isolated workspace."
</announcement>

<core_principle>
Git worktrees create isolated workspaces sharing the same repository. Systematic directory selection + safety verification = reliable isolation.
</core_principle>

<directory_selection>
Priority order: 1) Check existing: ls -d .worktrees 2>/dev/null then ls -d worktrees 2>/dev/null. If both exist, .worktrees wins. 2) Check CLAUDE.md: grep -i "worktree.*director" CLAUDE.md. 3) Ask user with options: .worktrees/ (project-local, hidden) or ~/.config/superpowers/worktrees/project-name/ (global).
</directory_selection>

<safety_verification>
For project-local directories (.worktrees or worktrees), MUST verify ignored before creating: git check-ignore -q .worktrees 2>/dev/null. If NOT ignored: add to .gitignore, commit, then proceed. For global directory (~/.config/superpowers/worktrees): no verification needed.
</safety_verification>

<creation_workflow>
1. Detect project: project=$(basename "$(git rev-parse --show-toplevel)")
2. Check git-crypt: [ -d .git/git-crypt ] || grep -q "filter=git-crypt" .gitattributes
3. Create worktree:
   - Standard: git worktree add "$path" -b "$BRANCH_NAME" && cd "$path"
   - Git-crypt: git worktree add --no-checkout "$path" -b "$BRANCH_NAME" && cd "$path" && git-crypt unlock && git checkout HEAD
4. Auto-detect setup: package.json -> npm install | Cargo.toml -> cargo build | requirements.txt -> pip install -r | pyproject.toml -> poetry install | go.mod -> go mod download
5. Run tests for clean baseline. If fail: report and ask. If pass: report ready.
6. Report: "Worktree ready at full-path. Tests passing (N tests, 0 failures). Ready to implement feature-name."
</creation_workflow>

<session_persistence>
Maintain worktree isolation throughout session. If worktree breaks (CWD deleted, git-crypt issues): recreate it, never silently fall back to main. Never commit to main when user requested worktree isolation.
</session_persistence>

<development_workflow>
After worktree creation, follow complete lifecycle:

1. **Implement**: Write code in isolated worktree. Commit frequently to track progress.

2. **Rebuild**: Run rebuild script if available. If not possible (NixOS on different branch), do dry build: nix build --dry-run or equivalent to verify changes compile.

3. **Test**: Find appropriate testing method - use /tmux skill for services, run unit tests, manual verification. Ensure changes work before proceeding.

4. **Create PR**: Push branch and create PR with gh pr create. Include clear description of changes and test results.

5. **Leave worktree**: Do NOT delete worktree after PR. Keep locally for follow-up work after code review feedback.

6. **Restore main**: cd back to main workspace and rebuild from main branch. System returns to stable state while PR is pending.

This ensures: isolated development, tested changes before PR, stable system after PR creation, worktree available for review iterations.
</development_workflow>

<integration>
Called by: brainstorming (Phase 4), any skill needing isolation. Pairs with: finishing-a-development-branch (cleanup), executing-plans or subagent-driven-development (work happens here).
</integration>

<red_flags>
Never: create project-local worktree without verifying ignored, skip baseline tests, proceed with failing tests without asking, assume directory location, skip CLAUDE.md check, create in git-crypt repo without --no-checkout + unlock flow. Always: follow directory priority, verify ignored for project-local, check git-crypt first, auto-detect setup, verify clean baseline.
</red_flags>
