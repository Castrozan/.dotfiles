---
name: personal
description: Master index and discovery entry point for Lucas's personal skills and channels. Run the listing script to enumerate every personal skill and chapter on demand. Use when work touches a personal tool or platform, or the user names a topic this index covers.
---

This skill is the discovery entry point for every personal skill. None of them are auto-loaded; call this first, then read only the specific `SKILL.md` or chapter file you actually need.

## Listing all personal skills

Run from this skill's base directory:

```bash
python3 scripts/list-personal-skill-metadata.py
```

Optional custom vault path:

```bash
python3 scripts/list-personal-skill-metadata.py /path/to/personal-skill-vault
```

Returns JSON. Top-level skills include `name`, `description` (from frontmatter), `directory_name`, `path`, and `skill_markdown_path`. Chapter files inside umbrella skills include `name` (`<umbrella>/<chapter>`), `path`, and a short `preview` extracted from the file body. Read the specific files you need after inspecting the list.

## Umbrella chapters in this skill

This `personal` skill is also the umbrella for Lucas's personal channels and platforms. Each chapter lives in its own file so only the relevant one loads:

- `obsidian.md` — Obsidian vault operations (daily notes, TODO tracking, activity logging, ReadItLater inbox).

Scripts for some capabilities live in their original locations under `agents/skills/<capability>/scripts/`. Some capabilities (ponto, home-assistant) are pure Chrome DevTools MCP workflows with no scripts.
