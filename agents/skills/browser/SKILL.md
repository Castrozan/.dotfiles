---
name: browser
description: Use when user asks to open a webpage, scrape content, fill forms, click buttons, take screenshots, test a web UI, or automate any browser interaction. Also use when navigating authenticated web apps or testing frontend changes.
---

<how_it_works>
Chrome DevTools MCP connects to the user's real Google Chrome — real logins, real cookies, no automation detection. Chrome runs normally. The MCP server connects via DevToolsActivePort and a consent dialog ("Allow remote debugging?") appears. A background script auto-accepts it (focus Chrome, Tab to Allow, Enter). Sites see a normal browser, not an automated one.
</how_it_works>

<workflow>
1. `mcp__chrome-devtools__list_pages` — verify connection (auto-launches Chrome if needed)
2. `mcp__chrome-devtools__navigate_page` — go to URL
3. `mcp__chrome-devtools__take_snapshot` — see page elements with uid refs
4. `mcp__chrome-devtools__click` / `mcp__chrome-devtools__fill` — interact using uid from snapshot
5. `mcp__chrome-devtools__take_screenshot` — visual verification when needed
</workflow>

<connection_troubleshooting>
If MCP tools hang or fail:

1. **`scripts/verify-cdp-connection.sh`** — check DevToolsActivePort exists and port is listening
2. **`scripts/ensure-chrome-running.sh`** — launch Chrome normally, clean stale port files
3. **`scripts/accept-cdp-consent.sh`** — focus Chrome, Tab, Enter to accept the consent dialog

The consent dialog appears each time the MCP server connects. The wrapper auto-accepts it in a background loop (5 attempts). If it fails, run `accept-cdp-consent.sh` manually.
</connection_troubleshooting>

<available_tools>
navigate_page, click, fill, fill_form, take_screenshot, take_snapshot, evaluate_script, list_pages, new_page, close_page, select_page, wait_for, press_key, hover, drag, type_text, upload_file, handle_dialog, emulate, resize_page, get_console_message, list_console_messages, get_network_request, list_network_requests.
</available_tools>

<tips>
Always take a fresh snapshot after navigation or interaction — uids change between snapshots. Prefer snapshots over screenshots (less tokens). Use list_pages to see all open tabs.
</tips>
