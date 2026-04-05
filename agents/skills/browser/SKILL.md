---
name: browser
description: Use when user asks to interact with a live webpage - fill forms, click buttons, navigate authenticated apps, automate Electron apps, test UI, take screenshots. Do NOT use for fetching or reading web content programmatically - use curl, MCP fetch tools, or domain-specific skills instead.
---

<strategy>
Two browser MCPs are available. Browser Use (`mcp__browser-use__*`) is the primary tool - it launches its own Chrome, works immediately, handles general browsing and Electron apps. Chrome DevTools (`mcp__chrome-devtools__*`) connects to the user's real Chrome Global for stealth on sites that detect automation (Google, banking, Cloudflare). Read BROWSER-STRATEGY.md for the full decision framework.
</strategy>

<browser_use_workflow>
Works immediately with no setup. Launches its own Chrome instance.

1. `mcp__browser-use__browser_navigate` - go to URL
2. `mcp__browser-use__browser_get_state` - see page elements with index refs
3. `mcp__browser-use__browser_click` / `mcp__browser-use__browser_type` - interact using index from state
4. `mcp__browser-use__browser_screenshot` - visual verification when needed
5. `mcp__browser-use__browser_close_all` - clean up when done
</browser_use_workflow>

<chrome_devtools_workflow>
Connects to the user's real Chrome Global via `--autoConnect`. Chrome runs bare (no automation flags) so Google and bot-detecting sites see a normal browser. The user must enable `chrome://inspect/#remote-debugging` once (persists across restarts) and click Allow on the consent dialog once per Chrome session.

If `mcp__chrome-devtools__list_pages` returns "Could not connect to Chrome":
1. Run `hypr-summon-chrome-global` to launch Chrome Global for the user
2. Tell the user: "Enable chrome://inspect/#remote-debugging if not already on (persists across restarts). Then click Allow on the consent dialog that will appear when I connect."
3. Call `mcp__chrome-devtools__list_pages` - this call BLOCKS until the user clicks Allow on the consent dialog in Chrome. Do not call any other tools while waiting.

Once connected:
1. `mcp__chrome-devtools__list_pages` - verify connection
2. `mcp__chrome-devtools__navigate_page` - go to URL
3. `mcp__chrome-devtools__take_snapshot` - see page elements with uid refs
4. `mcp__chrome-devtools__click` / `mcp__chrome-devtools__fill` - interact using uid from snapshot
5. `mcp__chrome-devtools__take_screenshot` - visual verification when needed
</chrome_devtools_workflow>

<tips>
Browser Use: always get fresh state after navigation or interaction - element indices change. Prefer state over screenshots (less tokens).
Chrome DevTools: always take a fresh snapshot after navigation - uids change between snapshots. Prefer snapshots over screenshots.
</tips>
