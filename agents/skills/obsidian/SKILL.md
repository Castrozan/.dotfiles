---
name: obsidian
description: Manage the Obsidian vault — daily notes, TODO tracking, activity logging, and inbox processing. Use when user mentions daily note, wants to log activity, add/check TODOs, review pending tasks, plan their day, process saved items, or interact with the vault.
---

<vault_location>
Vault path: @homePath@/vault/
Daily notes: @homePath@/vault/daily-note/
CLI tool: daily-note (creates today's note and opens in $EDITOR)
Environment variable: OBSIDIAN_HOME=@homePath@/vault
</vault_location>

<daily_note_format>
One note per day named YYYY-MM-DD-daily-note.md. Structure:

# YYYY-MM-DD Daily Note with heading and filename subheading.

## TODO section with standard markdown checkboxes (- [ ] unchecked, - [x] checked). Subtasks use tab indentation.

## Last Daily Notes with unchecked tasks — auto-populated by the daily-note CLI from last 5 days. Do not manually edit this section.
</daily_note_format>

<reading>
Read today's note directly at the vault daily-note path using current date. If today's note doesn't exist, check the most recent file in the daily-note directory. Scan last few daily notes for pending tasks across recent days.
</reading>

<adding_todos>
Add new items to the ## TODO section after existing items. Format: - [ ] Clear, actionable description with optional tab-indented subtasks. Include context like project names, file paths, or links when relevant.
</adding_todos>

<checking_off>
Change - [ ] to - [x] to complete. Subtasks can be checked independently. Parent task only checked when all subtasks are done. Proactively offer to check off items when related work completes.
</checking_off>

<logging_activity>
Log completed work as already-checked TODO items: - [x] Description of what was done. Keeps a record of accomplishments alongside planned work.
</logging_activity>

<inbox_processing>
The ReadItLater Inbox folder in the vault contains saved links and content. When processing the inbox: classify each item (tweet, article, GitHub repo, video, note), summarize with key takeaways, tag with relevant Obsidian tags, rate relevance (must-read, interesting, reference, skip), and mark processed items with #agent-work-done tag. Skip YouTube saves (no transcript extraction) and dead links. Process in batches of 20 items.
</inbox_processing>

<sync>
Notes sync across devices via Obsidian Sync when the app is running. Open Obsidian locally before reading to get latest version. Be aware of concurrent edit conflicts — check note is current before editing.
</sync>

<behavior>
Check the daily note to understand what user is working on. After completing significant work, offer to log it. When user mentions new tasks, offer to add them. Never delete unchecked items — they carry forward automatically via the CLI. Respect the note structure: no custom sections or changed headers.
</behavior>
