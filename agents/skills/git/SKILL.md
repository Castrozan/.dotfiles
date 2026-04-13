---
name: git
description: Git operations — creating high-quality conventional commits with meaningful messages and disciplined staging, and searching commit history efficiently via layered dump-and-grep. Use when committing, staging changes, writing commit messages, investigating past decisions, finding when code changed, or tracing feature evolution through the repo's history.
---

Umbrella skill for git workflows. Each capability lives in its own file so only the relevant one loads into context.

For creating commits — conventional format, diff analysis, specific-file staging, commit message quality — read `commit.md`.

For searching git history — layered log dumps, fast text search across subjects/paths/patches, function evolution, when-did-X-change investigations — read `history.md`.

Both capabilities follow the repo rule: **never `git add -A` or `git add .`** — always stage specific files so parallel work in the working tree is not swept up accidentally.
