---
name: assistant-cron
description: Manage persistent assistant behavior via OpenClaw cron jobs. Use when the user asks to enable/disable an autonomous assistant mode, schedule recurring briefings/reminders, or keep background assistant routines running (morning brief, breaks, follow-ups, monitoring tasks).
---

<rules>
All job names start with `assistant-` (except `daily-pill-reminder`). One job per behavior — easy to enable/disable selectively. All jobs use --session isolated for full tool access. All jobs use --announce --channel discord --to DISCORD_DM_ID for delivery — the --to flag is required since isolated sessions cannot auto-discover the delivery target. Get the DM channel ID from the current session's inbound metadata. Discord delivery is handled by --announce automatically — never instruct the agent to send a Discord message manually. Address Lucas as "sir" in JARVIS style.
</rules>

<audio_playback_trap>
Isolated cron sessions CAN play audio through speakers, but the payload MUST include explicit step-by-step instructions for TTS + audio playback via exec with background: true. Without explicit exec instructions, agents will hallucinate that they played audio. Always include "Do NOT skip the exec step. Do NOT just claim you played audio." in the payload. Reference the talk-to-user skill for the audio pipeline.
</audio_playback_trap>

<job_definitions>
Jobs to create when enabling assistant mode (all America/Sao_Paulo timezone, via jarvis agent):

1. assistant-morning-brief: 0 8 * * * — search web for AI/OpenClaw/Claude news, summarize top 3-5 items, speak brief version via TTS
2. daily-pill-reminder: 0 9 * * * — one-sentence reminder for B12, vitamin D, creatine
3. assistant-break-reminder: 30 10,15 * * 1-5 — stretch/hydrate/screen-break nudge, vary wording
4. assistant-evening-work-wrap: 0 18 * * 1-5 — ask about workday wins/blockers, offer to help wrap up
5. assistant-late-night-wrap: 30 22 * * * — gentle wind-down nudge, suggest wrapping up

Use openclaw cron add --help for the exact syntax. Each job needs: --name, --agent jarvis, --cron, --tz, --session isolated, --announce, --channel discord, --to DISCORD_DM_ID, --timeout-seconds, --message with TTS instructions.
</job_definitions>

<enable_disable>
Enable: clean up stale assistant-*/daily-pill-reminder duplicates first (idempotent), create all jobs, verify with openclaw cron list, test one with openclaw cron run.
Disable: remove all jobs matching assistant-* and daily-pill-* prefixes, confirm none remain.
</enable_disable>

<reliability>
After enable, verify all jobs exist. Test at least one job for both TTS and Discord delivery. Check openclaw cron runs for failures after first scheduled run. If Discord delivery fails with "requires a target": --to is missing. If TTS fails: check speaker volume and talk-to-user skill.
</reliability>
