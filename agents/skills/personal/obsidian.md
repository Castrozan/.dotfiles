<vault_location>
Vault path: `$OBSIDIAN_HOME` (set in session environment). Daily notes: `$OBSIDIAN_HOME/daily-note/`. CLI tool: `daily-note` (creates today's note and opens in $EDITOR).
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
Inbox path: `$OBSIDIAN_HOME/ReadItLater Inbox/` (note the space in directory name - shell commands must quote it).

File structure: line 1 is `[[ReadItLater]] [[Type]]` where Type is Tweet, Article, Youtube, or Textsnippet. The type is already classified - do not re-classify. Below line 1: a heading with source link, then the captured content.

Processed marker: `#agent-work-done` appended to line 1. A processed file looks like `[[ReadItLater]] [[Tweet]] #agent-work-done`. Files missing this tag are unprocessed.

Finding unprocessed items (filenames contain spaces - naive `for f in $(ls)` breaks):
```
cd "$OBSIDIAN_HOME/ReadItLater Inbox" && ls -t *.md | while IFS= read -r f; do if ! grep -q '#agent-work-done' "$f"; then echo "$f"; fi; done
```

Every saved item was intentionally curated by the user. Read the full content before any judgment. Never dismiss, label as "low-signal", or skip without engaging with the material.

Processing workflow: read the full file content first - the content is already captured locally by ReadItLater. Present a brief summary to the user verbally. Append `#agent-work-done` to line 1. Do not modify file content beyond the tag. Do not add summaries, ratings, or extra tags to the file.

YouTube and Instagram saves: tag as done - content is not extractable from CLI. Do NOT skip them. Mark line 1 with `#agent-work-done`.

Textsnippet and empty Note files: often near-empty (accidental saves or clipboard grabs). Tag done quickly.

Multi-content files: some files contain multiple `[[ReadItLater]]` headers concatenated (e.g. multiple Reddit posts). Process as one unit, tag the first line.

Tweet media enrichment: when tweets contain `pic.twitter.com` or `t.co` links and the user asks about attached images or video, read this umbrella's `comms-twitter.md` sub-file for twikit-cli usage, and use the fxtwitter API for reliable media URLs without auth. Do not reach for the browser skill to view tweet content.
</inbox_processing>

<sync>
Vault syncs continuously via the `obsidian-headless-sync` systemd service. No need to open the Obsidian app. Check service status: `systemctl --user status obsidian-headless-sync`.
</sync>

<behavior>
Check the daily note to understand what user is working on. After completing significant work, offer to log it. When user mentions new tasks, offer to add them. Never delete unchecked items - they carry forward automatically via the CLI. Respect the note structure: no custom sections or changed headers.
</behavior>
