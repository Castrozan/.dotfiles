---
name: todo
description: Capture and manage Lucas's tasks in his Todoist list via the `todo` CLI: add, list, complete, reschedule, digest. Use when recording a reminder or follow-up, or checking what is pending.
---

<purpose>Todoist is Lucas's single task tracker across every horizon, today to months out, visible to him in the Todoist
app, browser extension, and phone. Record anything he must do or remember with `todo` rather than in notes or agent
memory, so it surfaces where he actually looks.</purpose>

<auth>The `todo` command resolves the API token from `~/.secrets/todoist-api-token` (the agenix secret), falling back to
`TODOIST_API_TOKEN`. It works headless on any of Lucas's machines with no in-agent token handling.</auth>

<semantics>A task added with no `--due` is intentionally an undated someday/long-horizon backlog item, not a mistake;
give it a date only when it becomes time-bound. `todo digest --json` returns `{overdue, today, someday}`, the shape the
planned 08:00 morning-briefing push consumes.</semantics>

<resume>When the task is a resumable job, work begun this session that Lucas or a later agent will continue, put `claude
--resume <id>` on the first line of `--description` so he gets a copy-paste one-liner back into this session with its
full context. Take the id from the `CLAUDE_CODE_SESSION_ID` env var and write its literal value into the description,
never the variable name, which in Lucas's own shell expands to nothing or a different session and resumes the wrong one.
The transcript is host-local, so the command only works on the machine that filed the task; name that host when it is
not obvious. Omit for standalone reminders that carry no session state.</resume>

<gotchas>Priority is Todoist-native where 4 is highest (UI p1), so `--priority 1` for "top priority" silently sets the
lowest instead. `--filter` takes Todoist's own query language (`today`, `overdue`, `no date`, `@label`, `#project`,
`p1`, boolean `|` and `&`). Run `todo --help` or `todo <command> --help` for the authoritative flag surface.</gotchas>
