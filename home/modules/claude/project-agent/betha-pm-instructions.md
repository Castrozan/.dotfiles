<project-specific-instructions>
These instructions are specific to the betha-pm project agent. They supplement the base PM instructions.

<daily-standup-report>
You MUST register a dedicated cron for the daily standup report on every session start, in addition to the heartbeat cron. This is a separate cron from the heartbeat - do not conflate them.

MANDATORY on every session start, after verifying the heartbeat cron:
1. Call CronList and check if a daily report cron exists (named "daily-standup-report" or matching the prompt below).
2. If missing, call CronCreate with:
   - cron: "27 8 * * 1-5" (8:27am weekdays - gives 3 minutes buffer before the 8:30 deadline)
   - recurring: true
   - durable: true
   - prompt: "Daily standup report. Today is a business day and it is 8:27am. Generate the daily standup report immediately. Check git log for yesterday's and today's activity, review .pm/HEARTBEAT.md for current state, check for blockers, and write a complete standup report. Post it to the project's communication channel. The report must be ready by 8:30am - do not wait for user input."
3. Call CronList again to verify registration succeeded.

The daily standup report covers:
- What was done yesterday (git activity, completed tasks, agent work)
- What is planned for today (pending tasks, priorities from HEARTBEAT.md)
- Blockers and risks (stale tasks, failing pipelines, unanswered follow-ups)
- People status (who is active, who has pending items)

The report must be posted to the configured communication channel by 8:30am on every business day. This is non-negotiable - the team depends on this report for their morning sync.
</daily-standup-report>
</project-specific-instructions>
