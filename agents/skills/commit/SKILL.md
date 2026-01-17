---
name: commit
description: Create high-quality git commits with conventional format, meaningful descriptions, and analysis of changes. Use when user asks to commit, stage changes, or prepare a commit message.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

# Commit Skill

Generate high-quality commits following repository conventions with proper analysis.

**Announce at start:** "I'm using the commit skill to analyze changes and create a commit."

## Overview

This skill analyzes staged/unstaged changes and generates conventional commit messages with meaningful descriptions. It works with any AI that can execute shell commands.

## Step 1: Gather Context

Run these commands in parallel to understand the current state:

```bash
# Repository state
git status --porcelain

# Staged changes (what will be committed)
git diff --cached --stat
git diff --cached

# Unstaged changes (for context)
git diff --stat

# Recent commit patterns (learn the style)
git log --oneline -15
git log --format="%s%n%b---" -10
```

## Step 2: Analyze Changes

For each changed file, understand:

1. **What changed**: Additions, deletions, modifications
2. **Why it matters**: Feature, bugfix, refactor, docs, etc.
3. **Scope**: Which module/component/area is affected
4. **Impact**: Breaking changes, dependencies affected

If changes are unstaged, ask user before staging:
```
Found unstaged changes in: [files]
Should I stage these for commit? [list specific files or patterns]
```

## Step 3: Determine Commit Type

| Type | When to Use |
|------|-------------|
| `feat` | New functionality for users |
| `fix` | Bug fix |
| `refactor` | Code restructuring without behavior change |
| `perf` | Performance improvement |
| `docs` | Documentation only |
| `chore` | Maintenance, dependencies, tooling |
| `test` | Adding/fixing tests |
| `style` | Formatting, whitespace (no logic change) |
| `revert` | Reverting previous commit |

## Step 4: Determine Scope

Scope is optional but helpful. Use the most specific applicable:

- Module name: `feat(auth): add OAuth support`
- File/component: `fix(navbar): correct dropdown z-index`
- Area: `docs(api): update endpoint examples`
- Multiple scopes: `feat(agents)(skills): add commit skill`

Skip scope for broad changes: `chore: update dependencies`

## Step 5: Write Subject Line

Rules:
- Imperative mood: "add" not "added" or "adds"
- Lowercase first letter
- No period at end
- Max 72 characters
- Focus on WHAT, not HOW

**Good:** `feat(auth): add password reset flow`
**Bad:** `feat(auth): Added the password reset functionality.`

## Step 6: Write Body (When Needed)

Include body when:
- Change is non-obvious
- Multiple related changes
- Breaking changes
- Design decisions worth documenting

Body format:
```
[blank line after subject]
Why this change was made. Context the subject doesn't convey.

Additional details if needed:
- Bullet points for multiple points
- Technical decisions
- Breaking change notes
```

Skip body for trivial changes: `fix: typo in error message`

## Step 7: Stage Files

Use specific files, never `git add -A` or `git add .`:

```bash
git add path/to/file1.ts path/to/file2.ts
```

Verify staging:
```bash
git diff --cached --stat
```

## Step 8: Create Commit

Use HEREDOC for proper formatting:

```bash
git commit -m "$(cat <<'EOF'
type(scope): subject line here

Body paragraph explaining why this change was made.
Additional context if needed.
EOF
)"
```

For simple commits without body:
```bash
git commit -m "type(scope): subject line"
```

## Step 9: Verify

```bash
git log -1 --stat
git status
```

## Examples from Repository

```
feat(agents): add ownership headers to all agent files

Adds HTML comment header to all agent/skill/rule files:
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

This prevents non-architect agents from modifying these files when user
is working outside the dotfiles repo (where CLAUDE.md governance rules
aren't loaded).
```

```
feat(scripts): add claude-exit to home-manager

Integrate bin/claude-exit into nix-managed scripts.
Uses procps for ps command dependency.
```

```
refactor(agents): separate NixOS patterns into specialized agents

Move repository-specific NixOS patterns from core.md to dotfiles-expert.
Add delegation guidance between dotfiles-expert and nix-expert:
- dotfiles-expert: repository patterns, file organization, secrets workflow
- nix-expert: Nix language, evaluation, derivations, ecosystem tools

Core rules now contain only general agent behavior.
```

```
fix: screensaver horizontal split
```

```
chore(claude): upgrade to v2.1.9
```

## Interactive Mode

If user invokes with no staged changes:

1. Show current status
2. List changed files with brief descriptions
3. Ask what to include
4. Proceed with staging and commit

If user provides a message hint (`/commit fix the login bug`):
- Use hint to guide commit message
- Still analyze changes for accuracy
- May override hint if it doesn't match actual changes

## Error Handling

| Situation | Action |
|-----------|--------|
| No changes | Report "Nothing to commit" |
| Merge conflict markers | Refuse, ask user to resolve first |
| Large binary files | Warn before staging |
| Secrets (.env, credentials) | Refuse to stage, warn user |
| Pre-commit hook fails | Report error, suggest fixes, create NEW commit (never amend) |

## Red Flags

**Never:**
- Stage unrelated files (user may have parallel work)
- Use `git add -A` or `git add .`
- Commit secrets or credentials
- Use `--amend` unless explicitly requested AND safe
- Skip analyzing what actually changed
- Generate vague messages like "fix bug" or "update code"

**Always:**
- Read the actual diff before writing message
- Match repository's commit style
- Stage files explicitly by path
- Include body for non-trivial changes
- Verify commit succeeded

## Quick Reference

```
# Full workflow
git status --porcelain
git diff --cached
git log --oneline -10
git add specific/files.ts
git commit -m "$(cat <<'EOF'
type(scope): imperative subject

Why this change matters.
EOF
)"
git log -1
```
