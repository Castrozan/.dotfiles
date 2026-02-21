---
name: assistant-cron
description: Manage persistent assistant behavior via OpenClaw cron jobs. Use when the user asks to enable/disable an autonomous assistant mode, schedule recurring briefings/reminders, or keep background assistant routines running (morning brief, breaks, follow-ups, monitoring tasks).
---

# Assistant Cron

Use this skill to run a toggleable assistant mode through OpenClaw cron jobs.

## Rules

- Create jobs with names starting with `assistant-`.
- Prefer one job per behavior (easy to disable selectively).
- For recurring assistant behavior, use `sessionTarget: main` + `payload.kind: systemEvent`.
- Put explicit execution instructions in `payload.text` (what to check, what to send, where to send).
- Keep messages short and actionable.

## Enable assistant mode

1. `cron.list` and remove stale `assistant-*` jobs if duplicates exist.
2. Add baseline jobs (example set below):
   - `assistant-morning-brief`
   - `assistant-break-reminder`
   - `assistant-evening-wrap`
3. Confirm with `cron.list`.

## Disable assistant mode

1. `cron.list`
2. Remove all jobs with name prefix `assistant-`
3. Confirm no `assistant-*` jobs remain.

## Baseline job templates

### 1) Morning brief (08:00 local)

- schedule: `{"kind":"cron","expr":"0 8 * * *","tz":"America/Sao_Paulo"}`
- payload text should instruct: gather top updates relevant to Lucas (OpenClaw, AI agents, Claude Code), then send concise morning brief.

### 2) Break reminder (10:30 and 15:30 weekdays)

- schedule: `{"kind":"cron","expr":"30 10,15 * * 1-5","tz":"America/Sao_Paulo"}`
- payload text should instruct: send brief reminder to hydrate/stretch.

### 3) Evening wrap (18:00 weekdays)

- schedule: `{"kind":"cron","expr":"0 18 * * 1-5","tz":"America/Sao_Paulo"}`
- payload text should instruct: ask for daily wrap and pending priorities.

## Reliability checks

- After create/update/remove, check `cron.runs` for failures.
- If a run fails, fix payload text first (clearer instructions), then rerun.
- Keep idempotent: re-running enable should not duplicate jobs.
