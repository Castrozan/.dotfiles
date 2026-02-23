---
name: assistant-cron
description: Manage persistent assistant behavior via OpenClaw cron jobs. Use when the user asks to enable/disable an autonomous assistant mode, schedule recurring briefings/reminders, or keep background assistant routines running (morning brief, breaks, follow-ups, monitoring tasks).
---

# Assistant Cron

Toggleable assistant mode through OpenClaw cron jobs. Each job **speaks through PC speakers** via TTS and the cron delivery system **announces the result to Discord** automatically.

## Rules

- All job names start with `assistant-` (except `daily-pill-reminder`).
- One job per behavior — easy to enable/disable selectively.
- All jobs use `--session isolated` for full tool access.
- All jobs use `--announce --channel discord --to <discord_dm_channel_id>` for delivery.
  - The `--to` flag is **required** — isolated sessions cannot auto-discover the delivery target.
  - Get Lucas's Discord DM channel ID from the current session's inbound metadata (`chat_id` field).
- The agent payload should instruct to **speak via TTS through speakers only**. Discord delivery is handled by the `--announce` flag automatically — do NOT instruct the agent to send a Discord message manually.
- Address Lucas as "sir" in JARVIS style. Keep spoken parts brief (1-2 sentences).

## Enable assistant mode

1. Run `openclaw cron list` — remove any stale `assistant-*` or `daily-pill-reminder` duplicates.
2. Determine Lucas's Discord DM channel ID (from inbound metadata or ask).
3. Create all jobs below using `openclaw cron add`, replacing `DISCORD_DM_ID` with the actual ID.
4. Verify with `openclaw cron list`.
5. Test one job with `openclaw cron run <id>` to confirm both TTS and Discord delivery work.

## Disable assistant mode

1. `openclaw cron list`
2. Remove ALL jobs with name prefix `assistant-` AND `daily-pill-reminder`:
   ```bash
   openclaw cron list --json | jq -r '.jobs[] | select(.name | test("^(assistant-|daily-pill)")) | .id' | while read id; do openclaw cron rm "$id"; done
   ```
3. Confirm no assistant jobs remain with `openclaw cron list`.

## Job Definitions

Replace `DISCORD_DM_ID` with Lucas's actual Discord DM channel ID in all commands below.

### 1) Morning Brief — `assistant-morning-brief`

**Schedule:** `0 8 * * *` (8:00 AM daily, America/Sao_Paulo)

```bash
openclaw cron add \
  --name assistant-morning-brief \
  --agent jarvis \
  --cron "0 8 * * *" \
  --tz America/Sao_Paulo \
  --session isolated \
  --announce \
  --channel discord \
  --to DISCORD_DM_ID \
  --timeout-seconds 180 \
  --message "Morning brief for Lucas. Search the web for latest news about: OpenClaw AI, Claude Code, AI agents, and Anthropic. Summarize the top 3-5 most relevant items in a concise morning briefing. Keep it under 300 words. Then speak a shorter spoken version (under 30 seconds) through PC speakers using TTS (read the talk-to-user skill). Address Lucas as 'sir' in JARVIS style. The Discord message is sent automatically by the cron system — do NOT send one manually."
```

### 2) Daily Pill Reminder — `daily-pill-reminder`

**Schedule:** `0 9 * * *` (9:00 AM daily, America/Sao_Paulo)

```bash
openclaw cron add \
  --name daily-pill-reminder \
  --agent jarvis \
  --cron "0 9 * * *" \
  --tz America/Sao_Paulo \
  --exact \
  --session isolated \
  --announce \
  --channel discord \
  --to DISCORD_DM_ID \
  --timeout-seconds 60 \
  --message "It's 9 AM — time for Lucas's daily supplements (B12, vitamin D, creatine). Speak a one-sentence reminder through PC speakers using TTS (read the talk-to-user skill). Be JARVIS-style, address him as 'sir'. The Discord message is sent automatically by the cron system — do NOT send one manually."
```

### 3) Break Reminder — `assistant-break-reminder`

**Schedule:** `30 10,15 * * 1-5` (10:30 AM and 3:30 PM weekdays, America/Sao_Paulo)

```bash
openclaw cron add \
  --name assistant-break-reminder \
  --agent jarvis \
  --cron "30 10,15 * * 1-5" \
  --tz America/Sao_Paulo \
  --session isolated \
  --announce \
  --channel discord \
  --to DISCORD_DM_ID \
  --timeout-seconds 60 \
  --message "Break reminder for Lucas. Speak a one-sentence reminder through PC speakers using TTS (read the talk-to-user skill) telling him to stretch, hydrate, look away from screens. Vary the wording each time. JARVIS style. The Discord message is sent automatically by the cron system — do NOT send one manually."
```

### 4) Evening Work Wrap — `assistant-evening-work-wrap`

**Schedule:** `0 18 * * 1-5` (6:00 PM weekdays, America/Sao_Paulo)

```bash
openclaw cron add \
  --name assistant-evening-work-wrap \
  --agent jarvis \
  --cron "0 18 * * 1-5" \
  --tz America/Sao_Paulo \
  --session isolated \
  --announce \
  --channel discord \
  --to DISCORD_DM_ID \
  --timeout-seconds 90 \
  --message "Evening work wrap for Lucas. Speak a brief message through PC speakers using TTS (read the talk-to-user skill) asking about his workday — any wins, blockers, or priorities for tomorrow. Offer to help wrap up. JARVIS style, address as 'sir'. Keep spoken part under 15 seconds. The Discord message is sent automatically by the cron system — do NOT send one manually."
```

### 5) Late Night Wrap — `assistant-late-night-wrap`

**Schedule:** `30 22 * * *` (10:30 PM daily, America/Sao_Paulo)

```bash
openclaw cron add \
  --name assistant-late-night-wrap \
  --agent jarvis \
  --cron "30 22 * * *" \
  --tz America/Sao_Paulo \
  --session isolated \
  --announce \
  --channel discord \
  --to DISCORD_DM_ID \
  --timeout-seconds 90 \
  --message "Late night wrap for Lucas — it's 10:30 PM. Speak through PC speakers using TTS (read the talk-to-user skill) gently nudging him to wind down. Suggest wrapping up, jotting down tomorrow's priorities, and preparing for sleep. JARVIS style, address as 'sir'. Keep it warm but firm, two sentences max. The Discord message is sent automatically by the cron system — do NOT send one manually."
```

## Reliability checks

- After enable, run `openclaw cron list` to verify all 5 jobs exist and are enabled.
- Test at least one job: `openclaw cron run <id>` — confirm both TTS speaker output and Discord message delivery.
- Check `openclaw cron runs` for any failures after first scheduled run.
- If Discord delivery fails with "requires a target": ensure `--to` is set on the job.
- If TTS fails: check speaker volume and `talk-to-user` skill availability.
- Enable is idempotent: always clean up existing jobs before creating new ones.
