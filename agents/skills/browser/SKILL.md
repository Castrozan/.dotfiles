---
name: browser
description: Use when user asks to open a webpage, scrape content, fill forms, click buttons, take screenshots, test a web UI, or automate any browser interaction. Also use when navigating authenticated web apps or testing frontend changes.
---

<architecture>
Two browser access modes. The chrome-devtools MCP tools are available as native Claude Code tools (mcp__chrome-devtools__*). Use them directly — no Bash wrappers needed.

1. **Chrome DevTools MCP** (primary) — native MCP tools attached to user's real Google Chrome session. Real logins, real cookies, no automation detection, no CAPTCHAs. Tools: navigate_page, click, fill, fill_form, take_screenshot, take_snapshot, evaluate_script, list_pages, new_page, select_page, wait_for, press_key, hover, drag, upload_file, handle_dialog.

2. **agent-browser CLI** (secondary) — native Rust CLI via Bash, 200-400 tokens per snapshot. Use when Chrome is unavailable or for parallel headless sessions. Commands: open, snapshot -i, click @ref, fill @ref "text", screenshot, get text, press, wait.
</architecture>

<when_to_use_what>
Default to Chrome DevTools MCP for everything — it uses the user's authenticated Chrome session.

Use agent-browser only when: running parallel headless sessions, Chrome is not running, or you need the CLI for a script.
</when_to_use_what>

<chrome_devtools_mcp>
Call MCP tools directly: mcp__chrome-devtools__navigate_page, mcp__chrome-devtools__click, etc.

Workflow: navigate_page to URL → take_snapshot to see page elements with uid refs → click/fill using uid → take_screenshot for visual verification.

The snapshot returns an accessibility tree with uid identifiers. Use these uids for click and fill operations. Always take a fresh snapshot after navigation or interaction — uids change between snapshots.

Chrome must be running with remote debugging enabled (chrome://inspect/#remote-debugging). The toggle is persisted automatically by the Nix configuration. If connection fails, verify Chrome is running with: pgrep -f google-chrome
</chrome_devtools_mcp>

<agent_browser_cli>
Run via Bash tool. Core workflow: open URL → snapshot -i → interact with @refs → re-snapshot.

Essential commands:
- `agent-browser open <url>` — navigate
- `agent-browser snapshot -i` — interactive elements with @e1, @e2 refs
- `agent-browser click @e1` — click by ref
- `agent-browser fill @e2 "text"` — fill input
- `agent-browser press Enter` — press key
- `agent-browser screenshot` — capture to file
- `agent-browser get text body` — page text
- `agent-browser --auto-connect open <url>` — attach to running Chrome
</agent_browser_cli>

<token_costs>
Chrome DevTools snapshot: ~500-2000 tokens (full a11y tree). agent-browser snapshot: ~200-400 tokens (compact refs). Screenshot: ~1500 tokens. Prefer snapshots over screenshots. Skip observation for predictable outcomes.
</token_costs>
