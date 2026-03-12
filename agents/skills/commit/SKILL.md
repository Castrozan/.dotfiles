---
name: commit
description: Create high-quality git commits with conventional format, meaningful descriptions, and analysis of changes. Use when user asks to commit, stage changes, or prepare a commit message.
---

<announcement>
"I'm using the commit skill to analyze changes and create a commit."
</announcement>

<context_gathering>
Run in parallel: git status, git diff (cached and unstaged), git log (recent commits and their format). Understand all changes before writing any message.
</context_gathering>

<analysis>
For each changed file determine: what changed, why it matters (feature, bugfix, refactor, docs), scope (module, component, area), and impact (breaking changes, dependencies). Read actual diffs — never generate messages from filenames alone.
</analysis>

<format>
Conventional commits: type(scope): subject. Imperative mood ("add" not "added"), lowercase, no period, max 72 chars. Include body when change is non-obvious, multiple related changes, or breaking. Match the repo's existing commit style — check recent log.
</format>

<staging>
Always use specific files, never git add -A or git add . to avoid staging unrelated parallel work. Verify staged content matches intent with git diff --cached.
</staging>

<red_flags>
Never: stage unrelated files, commit secrets, skip analyzing actual diff, generate vague messages. Always: read actual diff, stage files by path, include body for non-trivial changes, verify success.
</red_flags>
