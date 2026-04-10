<heartbeat-setup>
On session start, register a heartbeat cron via CronCreate. Crons are session-scoped - they live only while the Claude Code process is running. The cron fires while the REPL is idle, never interrupting active work.

The bootstrap prompt (sent by the launch script on startup) registers the heartbeat cron automatically. If the session restarts, the launch script sends the bootstrap again and the cron is re-registered. No manual setup needed.

Default interval: every 30 minutes. Pick an off-minute to avoid API congestion (e.g., `3,33 * * * *` instead of `0,30 * * * *`).

The heartbeat prompt should be short and direct:

```
Heartbeat tick. Read HEARTBEAT.md. If there are pending tasks with elapsed intervals, work on the highest priority one. If nothing needs attention, do nothing - do not respond or log.
```

Recurring crons auto-expire after 7 days. For persistent agents that run longer, the agent should re-register the heartbeat if it notices no cron is active (check via CronList).
</heartbeat-setup>

<heartbeat-md-format>
HEARTBEAT.md supports two sections: free-form notes at the top and structured tasks below.

Free-form section is plain markdown - current priorities, blockers, reminders. The agent reads it on each tick for situational awareness.

Structured tasks use a simple format:

```markdown
## Tasks

- [ ] task-name | interval | prompt or description
- [ ] task-name | once | prompt or description
- [x] task-name | done | completed note
```

Interval values: `30m`, `1h`, `2h`, `daily`, `once` (fire once then mark done).

The agent tracks when each task last ran using timestamps appended inline:

```markdown
- [ ] check-pipeline | 1h | verify CI pipeline is green | last: 2026-04-10T15:30
- [ ] review-open-mrs | daily | check for MRs awaiting review | last: 2026-04-10T09:00
- [x] send-status-report | once | send weekly status to team | done: 2026-04-10T14:00
```

On each heartbeat tick, the agent:
1. Reads HEARTBEAT.md
2. Finds tasks whose interval has elapsed since their `last:` timestamp
3. Picks the highest priority eligible task (top of list = highest priority)
4. Executes it
5. Updates the `last:` timestamp
6. If no tasks are eligible, does nothing
</heartbeat-md-format>

<autonomous-work>
The agent works autonomously on heartbeat tasks. It has the same tools as any interactive session - skills, MCP servers, browser, file operations, messaging. It can:

- Read and update project files
- Run commands and scripts
- Use browser for research or web interactions
- Send messages via Discord, Google Chat, or other configured channels
- Create and manage tasks
- Delegate to sub-agents for implementation
- Commit code changes

The project CLAUDE.md defines what the agent is allowed to do autonomously vs what requires user confirmation. By default, follow the same rules as core.md: freely take local reversible actions, confirm before actions that affect shared systems or are hard to reverse.
</autonomous-work>

<active-hours>
If the project CLAUDE.md defines active hours (e.g., `active_hours: 09:00-22:00`), the heartbeat should skip ticks outside those hours. Check current time on each tick and return immediately if outside the window.
</active-hours>

<cost-awareness>
Each heartbeat tick consumes tokens even if no work is done. The prompt should be minimal. If HEARTBEAT.md says "No active work" and there are no structured tasks with elapsed intervals, the agent should do nothing without generating a verbose response.

For projects with low activity, increase the heartbeat interval (e.g., every 2 hours instead of 30 minutes). The interval is set in the bootstrap prompt and can be adjusted by editing the cron.
</cost-awareness>
