---
name: personal
description: Lucas's personal life and platforms — autonomous assistant monitoring loop across Gmail, Google Calendar, WhatsApp, and Google Chat; Obsidian vault for daily notes, TODOs, and ReadItLater inbox; Google Chat messaging and webhooks; Twitter/X (x.com, twitter.com) scraping, posting, tweets, profiles, trends, media, tweet URL resolution; VTuber avatar lip sync and expressions; Senior Gestão de Ponto time-entry automation (marcações, acertos); smart home control via Home Assistant (lights, AC); phone status over SSH (battery, charging, uptime); OpenClaw multi-agent platform (grid, A2A, Telegram bots, cron). Use for any task about Lucas's personal channels, notes, tweets, social media URLs, smart home, phone, work time-tracking, or openclaw.
---

Umbrella skill covering Lucas's personal communication, tools, home, and agent platforms. Each capability lives in its own file so only the relevant one loads into context.

For the autonomous monitoring loop (5-minute heartbeat across Gmail, Calendar, WhatsApp, Google Chat with triage and Discord escalation), read `assistant.md`. Inside that workflow: Gmail (`assistant-gmail.md`), Calendar (`assistant-calendar.md`), WhatsApp + Google Chat (`assistant-chat.md`).

For on-demand Google Chat and WhatsApp monitoring and replies (not the full loop, just "check and respond"), read `chat-monitor.md`.

For Obsidian vault operations — daily notes, TODO tracking, activity logging, ReadItLater inbox processing — read `obsidian.md`.

For communications tooling — Google Chat browser automation and webhooks (`comms-google-chat.md`), Twitter/X scraping and posting (`comms-twitter.md`), VTuber avatar lip sync and expressions (`comms-avatar.md`).

For Senior Gestão de Ponto time-entry automation (pinchtab + CDP WebSocket scripts for clock-in marcações), read `ponto.md`.

For Home Assistant smart home control (Tuya lights via ha-light, Midea AC via ha-ac), read `home-assistant.md`.

For remote phone status over SSH (battery, charging, uptime, storage), read `phone.md`.

For the OpenClaw multi-agent platform — grid coordination (`openclaw-grid.md`), A2A protocol (`openclaw-a2a.md`), cron jobs and recurring tasks (`openclaw-cron.md`), and the top-level platform overview (`openclaw.md`).

Scripts for each capability still live in their original locations under `agents/skills/<capability>/scripts/` and are referenced by Nix modules.
