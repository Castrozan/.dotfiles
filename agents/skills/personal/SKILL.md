---
name: personal
description: Master index for every personal skill — discover what is available without loading the full set into context. Run the listing script to enumerate top-level skills (git, nix, browser, comms, openclaw, review, session, test, ...) and umbrella chapters (Lucas's channels — Gmail, Calendar, WhatsApp, Google Chat, Obsidian, Twitter/X, Ponto, Home Assistant, phone status). Use whenever work might benefit from a personal-only skill, or when the user mentions any topic this index covers.
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

- `assistant.md` — autonomous monitoring loop (5-minute heartbeat across Gmail, Calendar, WhatsApp, Google Chat with triage and Discord escalation). Sub-files: `assistant-gmail.md`, `assistant-calendar.md`, `assistant-chat.md`.
- `chat-monitor.md` — on-demand Google Chat and WhatsApp monitoring and replies (not the full loop).
- `obsidian.md` — Obsidian vault operations (daily notes, TODO tracking, activity logging, ReadItLater inbox).
- `ponto.md` — Senior Gestao de Ponto time-entry automation (Chrome DevTools MCP for clock-in marcacoes).
- `home-assistant.md` — Home Assistant smart home control (Tuya lights via ha-light, Midea AC via ha-ac).
- `skills/phone-status/SKILL.md` — remote phone status over SSH (battery, charging, uptime, storage).
- `openclaw.md`, `openclaw-grid.md`, `openclaw-a2a.md`, `openclaw-cron.md` — OpenClaw multi-agent platform (grid coordination, A2A protocol, cron jobs and recurring tasks, top-level platform overview).

Scripts for some capabilities live in their original locations under `agents/skills/<capability>/scripts/`. Some capabilities (ponto, home-assistant) are pure Chrome DevTools MCP workflows with no scripts.
