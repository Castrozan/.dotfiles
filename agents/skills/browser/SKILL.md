---
name: browser
description: Use when user asks to open a webpage, scrape content, fill forms, click buttons, take screenshots, test a web UI, or automate any browser interaction. Also use when navigating authenticated web apps or testing frontend changes.
---

<how_it_works>
Chrome DevTools MCP server starts with Claude but does NOT launch Chrome or auto-connect. Chrome Global (class: chrome-global, user-data-dir: ~/.config/chrome-global) is launched on demand in the workflow step below, only when browser tools are actually needed. The MCP connects on first tool call after Chrome is available. Sites see a normal browser with real logins and cookies, not an automated one.
</how_it_works>

<workflow>
1. Ensure Chrome Global is running — run `hypr-summon-chrome-global` (launches if needed, focuses if already running)
2. `mcp__chrome-devtools__list_pages` — verify connection
3. `mcp__chrome-devtools__navigate_page` — go to URL
4. `mcp__chrome-devtools__take_snapshot` — see page elements with uid refs
5. `mcp__chrome-devtools__click` / `mcp__chrome-devtools__fill` — interact using uid from snapshot
6. `mcp__chrome-devtools__take_screenshot` — visual verification when needed
</workflow>

<connection_troubleshooting>
If MCP tools fail with "Could not connect to Chrome":

1. Verify Chrome Global is running: `hyprctl clients -j | jq '.[] | select(.class == "chrome-global")'`
2. Check DevToolsActivePort exists: `cat ~/.config/chrome-global/DevToolsActivePort`
3. If no DevToolsActivePort, Chrome was launched without --remote-debugging-port=0. Use SUPER+C (summon script) to relaunch.
4. If Chrome crashes: check for corrupted Sync Data LevelDB — remove `~/.config/chrome-global/Default/Sync Data/` and relaunch.
</connection_troubleshooting>

<available_tools>
navigate_page, click, fill, fill_form, take_screenshot, take_snapshot, evaluate_script, list_pages, new_page, close_page, select_page, wait_for, press_key, hover, drag, type_text, upload_file, handle_dialog, emulate, resize_page, get_console_message, list_console_messages, get_network_request, list_network_requests.
</available_tools>

<tips>
Always take a fresh snapshot after navigation or interaction — uids change between snapshots. Prefer snapshots over screenshots (less tokens). Use list_pages to see all open tabs.
</tips>
