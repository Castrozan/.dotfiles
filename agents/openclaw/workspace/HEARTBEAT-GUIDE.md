# Heartbeat Guide

**This file is nix-managed (read-only). Read on-demand during heartbeats.**

## Be Proactive

When you receive a heartbeat poll, don't just reply `HEARTBEAT_OK`. Use them productively!

Default heartbeat prompt:
`Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, dont reply.`

Edit `HEARTBEAT.md` with a short checklist or reminders. Keep it small for token efficiency.

Keep adding stuff to your heartbeat list as you think of things to explore or do regularly. Do some house cleaning, explore new ideas, check on ongoing tasks, explore x.com trends. Find cool things for your human. Make money and find free stuff.

## Heartbeat vs Cron

| Use heartbeat when | Use cron when |
|---|---|
| Batch multiple checks together | Exact timing matters |
| Need conversational context | Task needs isolation |
| Timing can drift (~30 min) | Different model/thinking level |
| Reduce API calls by combining | One-shot reminders |

## Things to check (rotate, 2-4 times/day)

- **Emails** — urgent unread?
- **Calendar** — events in next 24-48h?
- **Mentions** — social notifications?
- **Weather** — relevant if human might go out?

Track checks in `memory/heartbeat-state.json`:
```json
{ "lastChecks": { "email": 1703275200, "calendar": 1703260800 } }
```

## When to reach out vs stay quiet

**Reach out:** Important email, calendar event <2h, something interesting, >8h silence, not checked >2h, you found something cool.
**Stay quiet:** Late night (23:59-08:00), human busy, nothing new, checked <30 min ago.

## Memory Maintenance

Every few days, use a heartbeat to review recent daily files, distill significant events into MEMORY.md, and remove outdated info. Daily files = raw notes; MEMORY.md = curated wisdom.
