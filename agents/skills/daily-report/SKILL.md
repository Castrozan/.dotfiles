---
name: daily-report
description: Manage today's daily manager report file. Use when the user asks to generate, update, or finalize their standup or manager update, or when a meaningful unit of work should be logged into today's report.
---

<announcement>
"I'm using the daily-report skill to update today's manager report."
</announcement>

<file_location>
One file per day at `manager-reports/<YYYY-MM-DD>-manager-report.md`, relative to the PM workspace root. The root is resolved at call time by walking up from cwd for a `.pm/HEARTBEAT.md` marker; the helper errors out when no marker is found. Multiple sessions may write the same file concurrently.
</file_location>

<helper_script>
All reads and writes go through `scripts/daily-report.py`; run `--help` for subcommands. Pass `--date YYYY-MM-DD` to target a non-today date. Never `Edit`/`Write` the file directly: direct writes bypass the `fcntl.flock` and silently drop concurrent entries from parallel sessions.
</helper_script>

<file_format>
Three sections, in order: `Blockers: <value-or-None>`, `Today:`, `Next:`. Bullets are four-space indented then `- `. No headers, separators, or commentary lines; the file is sent to the manager as-is.
</file_format>

<entry_writing_rules>
Prefix every bullet with the ticket id (`CAFE-529:`); it anchors the entry for the manager. Write in plain manager-readable English: no file paths, function names, hook names, class names, internal modules, or stack-trace jargon. One bullet captures one outcome; merge investigation, implementation, and verification of the same fix into one bullet. Never reference an MR or PR by number alone; use `the <short description> MR (!<number>)` so the manager understands without opening GitLab. When summarising an MR, read its description via `glab` `mr-view <id>` and lift the user-facing impact, not the implementation detail. Outcomes over activities. No em dashes; use a comma, a regular hyphen-dash surrounded by spaces, or rewrite. Keep each bullet to roughly one screen line. The Next section lists concrete handoffs (`ask the team to review`, `monitor X reaching QA`, `kick off Y`), not aspirations.
</entry_writing_rules>

<tone_anchor>
The user's accepted canonical tone reference:

```
Blockers: None
Today:
    - CAFE-529: fixed the underlying bug breaking active users every 15 minutes, added activity-aware silent refresh so the modal only opens for truly idle users (stay signed in / sign out with 30s countdown)
    - CAFE-529: rebased the session-timeout MR (!100) onto develop, full end-to-end tested all the flows
    - CAFE-522: merged the post-deploy follow-ups MR (!101), duplicate-code field error in the restaurant modal, lambda timing out on Secrets Manager, Quebec city rename so the 21 Québec restaurants stop being skipped on each sync
Next:
    - CAFE-529: ask the team to review the session-timeout MR (!100)
    - CAFE-522: monitor the post-deploy follow-ups MR (!101) reaching QA and ask Vlad for the log dump
    - CAFE-534: kick off the DPS 2.0 equivalent
```

Match this register: declarative, outcome-led, light on adjectives, no engineering nouns the manager would not recognize.
</tone_anchor>

<workflow_log_during_the_day>
When a meaningful unit of work finishes in any session: 1) `show` the file to avoid duplicates; 2) if an existing bullet on the same ticket can absorb the new fact, `remove-today` + `add-today` a merged bullet instead of creating a second bullet for the same ticket; 3) pull MR or ticket context before writing the bullet; 4) append via `add-today`/`add-next`; use `set-blockers` only for a real blocker the user named.
</workflow_log_during_the_day>

<workflow_generate_full_report>
When the user asks for the day's report: 1) `show` the current file as the working draft; 2) gather activity from every wired source (`git log --since=midnight --author=<user>` across mandate repos, `glab user-events --host both`, `jira` ticket transitions, and any other wired data source); 3) decide Today vs Next for each unlogged item and append via the helper; 4) re-`show` and present the file verbatim. The file stays on disk as the day's archive.
</workflow_generate_full_report>

<concurrency_trap>
`fcntl.flock` serializes writers but does not merge intent: two sessions appending "CAFE-529: fixed X" produce two near-duplicate bullets. Always `show` before `add-*`, and prefer `remove-*` + `add-*` to consolidate when a parallel session left a duplicate.
</concurrency_trap>
