---
name: git
description: Git operations: creating high-quality conventional commits with meaningful messages and disciplined staging, and searching commit history efficiently via cached log dumps. Use when committing, staging changes, writing commit messages, investigating past decisions, finding when code changed, or tracing feature evolution through the repo's history.
---

<context_gathering>
Run in parallel: git status, git diff (cached and unstaged), git log (recent commits and their format). Understand all
changes before writing any message.
</context_gathering>

<analysis>
For each changed file determine: what changed, why it matters (feature, bugfix, refactor, docs), scope (module,
component, area), and impact (breaking changes, dependencies). Read actual diffs; never generate messages from filenames
alone.
</analysis>

<format>
Conventional commits: type(scope): subject. Imperative mood ("add" not "added"), lowercase, no period, max 72 chars.
Include body when change is non-obvious, multiple related changes, or breaking.
</format>

<staging>
Never git add -A or git add . to avoid staging unrelated parallel work.
</staging>

<history_search>
Use the `git-history` command for any exploratory commit search instead of repeated `git log --grep` or `git log -G`
calls; those rescan the full object store every time. `git-history` dumps the log to /tmp once, after which any grep
against the dump is instant and reusable across queries. Run `git-history --help` for the layered workflow, search
patterns, and cache behavior; `git-history info` shows current cache status. Skip the script for simple targeted lookups
like `git log -1 HEAD`, `git blame <file>`, or `git show <hash>`; those do not benefit from caching.
</history_search>
