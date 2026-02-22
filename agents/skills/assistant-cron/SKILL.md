---
name: assistant-cron
description: Manage persistent assistant behavior via OpenClaw cron jobs. Use when the user asks to enable/disable an autonomous assistant mode, schedule recurring briefings/reminders, or keep background assistant routines running (morning brief, breaks, follow-ups, monitoring tasks).
---

# Assistant Cron

Toggleable assistant mode through OpenClaw cron jobs. Each job sends a **Discord message** (for logging) and **speaks through PC speakers** via TTS (read the `talk-to-user` skill).

## Rules

- All job names start with `assistant-` (except `daily-pill-reminder`).
- One job per behavior — easy to enable/disable selectively.
- All jobs use `sessionTarget: isolated` for full tool access.
- All jobs use `--announce --channel discord` for delivery.
- Every job payload must instruct the agent to: (1) send a Discord message, (2) speak via TTS through speakers.
- Address Lucas as "sir" in JARVIS style. Keep spoken parts brief (1-2 sentences).

## Enable assistant mode

1. Run `openclaw cron list` — remove any stale `assistant-*` or `daily-pill-reminder` duplicates.
2. Create all jobs below using `openclaw cron add`.
3. Verify with `openclaw cron list`.
4. Test one job with `openclaw cron run <id>` to confirm Discord + TTS delivery works.

## Disable assistant mode

1. `openclaw cron list`
2. Remove ALL jobs with name prefix `assistant-` AND `daily-pill-reminder`:
   ```bash
   openclaw cron list --json | jq -r '.jobs[] | select(.name | test("^(assistant-|daily-pill)")) | .id' | while read id; do openclaw cron rm "$id"; done
   ```
3. Confirm no assistant jobs remain with `openclaw cron list`.

## Job Definitions

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
  --timeout-seconds 180 \
  --message "Morning brief for Lucas. Search the web for latest news about: OpenClaw AI, Claude Code, AI agents, and Anthropic. Summarize the top 3-5 most relevant items in a concise morning briefing. Keep it under 300 words. After composing the brief, do TWO things: 1) Send the brief as a Discord message using the message tool. 2) Speak a shorter spoken version (under 30 seconds) through PC speakers using TTS (read the talk-to-user skill). Address Lucas as 'sir' in JARVIS style."
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
  --timeout-seconds 60 \
  --message "It's 9 AM — time for Lucas's daily supplements. Do TWO things: 1) Send a Discord message reminding him to take his B12, vitamin D, creatine, and any other supplements. Be brief and JARVIS-style, address him as 'sir'. 2) Speak the reminder through PC speakers using TTS (read the talk-to-user skill). Keep the spoken version to one sentence."
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
  --timeout-seconds 60 \
  --message "Break reminder for Lucas. Do TWO things: 1) Send a Discord message reminding him to take a break — stretch, hydrate, look away from screens. Be brief, vary the wording, JARVIS style. 2) Speak the reminder through PC speakers using TTS (read the talk-to-user skill). Keep it to one sentence."
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
  --timeout-seconds 90 \
  --message "Evening work wrap for Lucas. Do TWO things: 1) Send a Discord message asking about his workday — any wins, blockers, or priorities for tomorrow. Offer to help wrap up loose ends. JARVIS style, address as 'sir'. 2) Speak a brief version through PC speakers using TTS (read the talk-to-user skill). Keep spoken part under 15 seconds."
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
  --timeout-seconds 90 \
  --message "Late night wrap for Lucas — it's 10:30 PM. Do TWO things: 1) Send a Discord message gently nudging him to wind down. Suggest wrapping up whatever he's working on, maybe jot down tomorrow's priorities, and start preparing for sleep. JARVIS style, address as 'sir'. Keep it warm but firm. 2) Speak the reminder through PC speakers using TTS (read the talk-to-user skill). Keep it to two sentences max."
```

## Reliability checks

- After enable, run `openclaw cron list` to verify all 5 jobs exist and are enabled.
- Test at least one job: `openclaw cron run <id>` — confirm both Discord message and speaker output.
- Check `openclaw cron runs` for any failures after first scheduled run.
- If a run fails, check payload clarity first, then rerun.
- Enable is idempotent: always clean up existing jobs before creating new ones.
