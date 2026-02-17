---
name: codewiki
description: Regenerate AI-consumable codebase documentation after significant structural changes. Use when you added/removed modules, reorganized directories, or completed a large refactor.
---

# codewiki

Generates structured markdown documentation from a repository for AI agent consumption. Uses repomix to pack the codebase and Claude Code CLI to produce architecture maps, module indexes, API docs, database schemas, and glossaries.

## When to run

Run codewiki when you have made **significant structural changes**:

- Added or removed nix modules in `home/modules/`
- Created new skills in `agents/skills/`
- Reorganized directory structure
- Added new scripts to `bin/`
- Changed database schemas or migrations
- Completed a large multi-file refactor

**Do not run** for minor changes (value tweaks, bug fixes, config adjustments). The docs are expensive to produce and small edits won't meaningfully change them.

## Usage

```bash
# Full regeneration — all 5 doc types
~/openclaw/monster/projects/codewiki/generate.sh ~/.dotfiles

# Partial — only regenerate specific areas
~/openclaw/monster/projects/codewiki/generate.sh --focus modules ~/.dotfiles
~/openclaw/monster/projects/codewiki/generate.sh --focus architecture,modules ~/.dotfiles

# Auto-detect which docs need regeneration from git diff
~/openclaw/monster/projects/codewiki/generate.sh --diff ~/.dotfiles
~/openclaw/monster/projects/codewiki/generate.sh --diff-from main ~/.dotfiles

# Dry run — pack repo and show size without generating
~/openclaw/monster/projects/codewiki/generate.sh --dry-run ~/.dotfiles
```

## Document types

| Area | File | What it covers |
|------|------|----------------|
| architecture | ARCHITECTURE.md | Overview, tech stack, project structure, component map, data flow |
| modules | MODULES.md | Module index, dependency graph, public interfaces |
| database | DATABASE.md | Schema, ER diagrams, migrations, query patterns |
| api | API.md | Endpoints, auth, request/response shapes |
| glossary | GLOSSARY.md | Domain terms, naming conventions, abbreviations |

## Output location

Docs are written to `docs/ai-context/` in the target repository. An `INDEX.md` is generated listing all available docs.

## Reading the docs

Before exploring source code, read `docs/ai-context/INDEX.md` to understand what documentation is available. Then read the specific document relevant to your task.

## Diff-based regeneration

The `--diff` flag inspects `git diff HEAD~1` to determine which doc types are affected:

- Changes in `*.nix`, `home/modules/`, `users/` → architecture, modules
- Changes in `agents/skills/` → modules, glossary
- Changes in `bin/`, scripts → api, modules
- Changes in `*migration*`, `*schema*`, `*db*` → database
- 20+ files changed → regenerate everything

Use `--diff-from <ref>` to diff against a specific branch or commit.
