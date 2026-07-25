---
name: obsidian
description: Manage the Obsidian vault (daily notes, TODO tracking, activity logging). Use when user mentions daily note, wants to log activity, add/check TODOs, review pending tasks, plan their day, or interact with the vault.
---

<vault_location>
Vault at '~/vault/', daily notes at '~/vault/daily-note/', CLI tool 'daily-note' creates today's note and opens in
'$EDITOR', environment variable 'OBSIDIAN_HOME' points at the vault root and is the path to prefer.
</vault_location>

<daily_note_format>
One note per day named YYYY-MM-DD-daily-note.md. Structure: top-level '# YYYY-MM-DD Daily Note' heading with filename
subheading; '## TODO' section with standard markdown checkboxes ('- [ ]' unchecked, '- [x]' checked, subtasks use tab
indentation); '## Last Daily Notes' with unchecked tasks, auto-populated by the daily-note CLI from the last 5 days (do
not manually edit this section).
</daily_note_format>

<reading>
Read today's note directly at the vault daily-note path using current date. If today's note doesn't exist, check the
most recent file in the daily-note directory. Scan last few daily notes for pending tasks across recent days.
</reading>

<adding_todos>
Add new items to the ## TODO section after existing items. Format: - [ ] Clear, actionable description with optional
tab-indented subtasks. Include context like project names, file paths, or links when relevant.
</adding_todos>

<checking_off>
Change - [ ] to - [x] to complete. Subtasks can be checked independently. Parent task only checked when all subtasks are
done. Proactively offer to check off items when related work completes.
</checking_off>

<logging_activity>
Log completed work as already-checked TODO items: - [x] Description of what was done. Keeps a record of accomplishments
alongside planned work.
</logging_activity>

<capture_inbox>
The vault ReadItLater Inbox is a capture zone owned by the knowledge-intake skill, which researches each capture and
turns it into a repo change or a filed entry. Never summarize, rate or mark captures from this skill; a capture
annotated in place reads as worked while nothing was learned or adopted.
</capture_inbox>

<sync>
Notes sync across devices via Obsidian Sync when the app is running. Open Obsidian locally before reading to get latest
version. Be aware of concurrent edit conflicts; check note is current before editing.
</sync>

<behavior>
Check the daily note to understand what user is working on. After completing significant work, offer to log it. When
user mentions new tasks, offer to add them. Never delete unchecked items; they carry forward automatically via the CLI.
Respect the note structure: no custom sections or changed headers.
</behavior>
