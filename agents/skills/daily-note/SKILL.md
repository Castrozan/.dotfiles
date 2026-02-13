---
name: daily-note
description: Manage Obsidian daily notes — personal activity log and TODO tracker. Use when user mentions daily note, wants to log activity, add/check TODOs, review pending tasks, or plan their day.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<overview>
The daily note is the user's personal log and task tracker. It lives in Obsidian and combines two things: a chronological record of what happened during the day, and a TODO list for tracking work. One note per day, named YYYY-MM-DD-daily-note.md.
</overview>

<paths>
Vault: @homePath@/vault/
Daily notes directory: @homePath@/vault/daily-note/
Today's note: @homePath@/vault/daily-note/YYYY-MM-DD-daily-note.md (use current date)
CLI tool: daily-note (creates today's note and opens it in $EDITOR)
Environment variable: OBSIDIAN_HOME=@homePath@/vault
</paths>

<note_format>
Each daily note follows this structure:

```markdown
# YYYY-MM-DD Daily Note
### YYYY-MM-DD-daily-note.md

## TODO

- [ ] Task description
	- [ ] Subtask with one tab indent
	- [x] Completed subtask
- [ ] Another task
- [x] Completed task

## Last Daily Notes with unchecked tasks

### previous-date-daily-note.md

- [ ] Carried-over unchecked items from previous days
```

Sections:
- **## TODO** — Active tasks for today. Mix of new tasks and carried-over items from previous days. Use standard markdown checkboxes (- [ ] unchecked, - [x] checked). Subtasks use tab indentation.
- **## Last Daily Notes with unchecked tasks** — Auto-populated by the daily-note CLI. Shows unchecked items from the last 5 days grouped by source note. Do not manually edit this section.
</note_format>

<reading_the_note>
To check current tasks and activity, read today's note directly:
  Read @homePath@/vault/daily-note/YYYY-MM-DD-daily-note.md

If today's note doesn't exist yet, look at the most recent file in the daily-note directory.

To find pending tasks across recent days, scan the last few daily notes. The daily-note CLI already carries forward unchecked items, but reading previous notes gives more context.
</reading_the_note>

<adding_todos>
Add new TODO items to the ## TODO section of today's note. Place them after existing items, before the blank lines above ## Last Daily Notes.

Format:
- [ ] Clear, actionable description
	- [ ] Subtask if the item has multiple steps
	- [ ] Another subtask

Keep descriptions specific enough to act on later. Include context like project names, file paths, or links when relevant.
</adding_todos>

<checking_off_todos>
To mark a task complete, change - [ ] to - [x]. Subtasks can be checked independently. A parent task should only be checked when all subtasks are done.

When the user completes work related to a daily note item, proactively offer to check it off.
</checking_off_todos>

<logging_activity>
The user may ask to log what they did. Add activity entries as TODO items that are already checked off:

- [x] Refactored authentication module
- [x] Reviewed PR #42 and left comments
- [x] Paired with team on deployment pipeline

This keeps a record of accomplishments alongside planned work.
</logging_activity>

<obsidian_sync>
Notes sync across devices via Obsidian Sync. Sync happens when Obsidian is open. To trigger sync:

1. Open Obsidian on the current machine (the app must be running for sync to work)
2. Wait a moment for sync to pull/push changes
3. Obsidian can be opened from the command line or app launcher

If the user edits notes on another device, open Obsidian locally before reading to get the latest version. When writing to a note, be aware that concurrent edits on another device could conflict — Obsidian handles merge conflicts, but it's best to check the note is current before editing.
</obsidian_sync>

<agent_behavior>
When working on tasks throughout the day:
- Check the daily note to understand what the user is working on and what's pending
- After completing significant work, offer to log it in the daily note
- When the user mentions new tasks, offer to add them to the TODO list
- When reviewing the day, summarize checked vs unchecked items
- Never delete unchecked items — they carry forward to the next day automatically via the CLI
- Respect the note structure: don't add custom sections or change headers
</agent_behavior>
