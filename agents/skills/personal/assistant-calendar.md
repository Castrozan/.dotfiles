<calendar-monitoring>
Google Calendar is accessed via the Google Calendar MCP tools (mcp__claude_ai_Google_Calendar__*). Authenticate on first use if needed.

**Check Workflow:**
1. Fetch today's remaining events and tomorrow's events
2. Check for events starting within 15 minutes - send reminder via Discord
3. Check for new invites - apply acceptance rules
4. Check for conflicts - flag via Discord
5. Update HEARTBEAT.md with next upcoming event

**Reminders:**
- 15 minutes before any event: send Discord reminder with event name, time, and meeting link if present
- Morning briefing (08:00): list today's events, highlight first meeting
- Do not remind about all-day events or declined events

**Invite Acceptance Rules:**

| Invite Type | Action |
|---|---|
| 1:1 with known colleague during work hours | Accept |
| Recurring team meeting (standup, retro, planning) | Accept |
| External meeting with unknown people | Escalate to Discord |
| Outside work hours (before 08:00 or after 18:00) | Escalate to Discord |
| Conflicts with existing event | Escalate with conflict details |
| Optional attendance marked | Tentative, inform via Discord |
| Weekend events | Escalate to Discord |

Work hours: Monday-Friday 08:00-18:00 BRT.

**Conflict Detection:**
When two events overlap:
1. Check which was created first (incumbent has priority)
2. Check if either is marked optional
3. Report to Discord: "[CONFLICT] Event A (10:00-11:00) overlaps Event B (10:30-11:30). A was scheduled first. Decline B?"

**Never Do:**
- Cancel existing events
- Create events without explicit instruction from Lucas
- Move events without permission
- Share calendar with new people
</calendar-monitoring>
