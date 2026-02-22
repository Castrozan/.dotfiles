---
name: commit
description: Create high-quality git commits with conventional format, meaningful descriptions, and analysis of changes. Use when user asks to commit, stage changes, or prepare a commit message.
---

<announcement>
"I'm using the commit skill to analyze changes and create a commit."
</announcement>

<context_gathering>
Run in parallel to understand current state:
  git status --porcelain
  git diff --cached --stat && git diff --cached
  git diff --stat
  git log --oneline -15
  git log --format="%s%n%b---" -10
</context_gathering>

<analysis>
For each changed file determine: what changed (additions, deletions, modifications), why it matters (feature, bugfix, refactor, docs), scope (module, component, area), and impact (breaking changes, dependencies).
</analysis>

<commit_types>
feat: new user functionality | fix: bug fix | refactor: restructuring without behavior change | perf: performance improvement | docs: documentation only | chore: maintenance, deps, tooling | test: adding/fixing tests | style: formatting only | revert: reverting previous commit
</commit_types>

<scope>
Optional but helpful. Use most specific: module name (feat(auth)), file/component (fix(navbar)), area (docs(api)), multiple (feat(agents)(skills)). Skip for broad changes: chore: update dependencies
</scope>

<subject_line>
Imperative mood ("add" not "added"), lowercase first letter, no period, max 72 chars, focus on WHAT not HOW. Good: feat(auth): add password reset flow. Bad: feat(auth): Added the password reset functionality.
</subject_line>

<body>
Include when: change is non-obvious, multiple related changes, breaking changes, design decisions worth documenting. Format: blank line after subject, explain WHY, bullet points for multiple items. Skip for trivial: fix: typo in error message
</body>

<staging>
Always use specific files, never git add -A or git add . to avoid staging unrelated parallel work. Verify with git diff --cached --stat.
</staging>

<red_flags>
Never: stage unrelated files, use git add -A or git add ., commit secrets, skip analyzing actual diff, generate vague messages. Always: read actual diff, match repo commit style, stage files by path, include body for non-trivial changes, verify success.
</red_flags>
