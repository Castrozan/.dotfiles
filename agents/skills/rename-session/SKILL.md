---
name: rename-session
description: Rename a Claude Code session for easier identification in /resume. Use when user wants to set a descriptive name for a session.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<prerequisites>
Requires new session name as argument. If not provided, ask user. The session must be closed (not the current active session) to appear in the index.
</prerequisites>

<execution>
rename-session "$PWD" "<session-name>"

Renames the most recently closed session in the current project. If user wants a specific session, they can provide the session ID as third argument.
</execution>

<output>
Show the script output confirming rename. Remind user the change will be visible in /resume.
</output>

<notes>
Modifies firstPrompt field in sessions-index.json. Active sessions don't appear in index until closed. If user tries to rename current active session, explain it will need to be done after ending this session.
</notes>
