---
name: browser
description: Use when user asks to open a webpage, scrape content, fill forms, click buttons, take screenshots, test a web UI, or automate any browser interaction. Also use when navigating authenticated web apps or testing frontend changes.
---

<how_it_works>
Chrome DevTools MCP is connected to the user's real Google Chrome with real logins, real cookies, no automation detection. Use the mcp__chrome-devtools__* tools directly.
</how_it_works>

<workflow>
1. `mcp__chrome-devtools__navigate_page` — go to URL
2. `mcp__chrome-devtools__take_snapshot` — see page elements with uid refs
3. `mcp__chrome-devtools__click` / `mcp__chrome-devtools__fill` — interact using uid from snapshot
4. `mcp__chrome-devtools__take_screenshot` — visual verification when needed
</workflow>

<available_tools>
navigate_page, click, fill, fill_form, take_screenshot, take_snapshot, evaluate_script, list_pages, new_page, close_page, select_page, wait_for, press_key, hover, drag, type_text, upload_file, handle_dialog, emulate, resize_page, get_console_message, list_console_messages, get_network_request, list_network_requests.
</available_tools>

<tips>
Always take a fresh snapshot after navigation or interaction — uids change between snapshots. Prefer snapshots over screenshots (less tokens). Use list_pages to see all open tabs. If Chrome is not running, tell user to launch Google Chrome.
</tips>
