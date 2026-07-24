---
name: jira
description: Manage Jira issues, sprints, epics, and boards via jira-cli. Use when user asks to create issues, check sprint status, move tickets, log work, or interact with Jira.
---

<announcement>
"I'm using the jira skill to interact with Jira."
</announcement>

<auth>
Token lives at ~/.secrets/jira-api-token (agenix). The helper reads it directly. Raw jira-cli reads JIRA_API_TOKEN from
the environment. Config: ~/.config/.jira/.config.yml. Auth type: 'basic' (email + API token).
</auth>

<helper_script>
scripts/jira-helper.py wraps jira-cli with --no-input and --plain. Run '--help' for subcommands. Prefer the helper; fall
back to jira-cli for interactive workflows or unsupported JQL.
</helper_script>

<non_interactive_trap>
jira-cli prompts interactively by default and hangs in non-interactive contexts. Always pass '--no-input' when running
from scripts or agents. The helper does this automatically.
</non_interactive_trap>

<filter_negation>
Negate filters with tilde prefix: '-s~Done' means "not Done", '-ax' means unassigned. This is non-obvious and not in
--help.
</filter_negation>

<batch_update_spam>
Use '--skip-notify' when editing multiple issues to avoid flooding team inboxes. Without it, each edit sends a Jira
notification.
</batch_update_spam>

<worklog_timezone>
Worklog entries default to server timezone. Always pass '--timezone' when logging time for users in different timezones,
or the hours land on the wrong day.
</worklog_timezone>
