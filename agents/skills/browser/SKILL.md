---
name: browser
description: Use when user asks to interact with a live webpage — fill forms, click buttons, navigate authenticated apps, automate Electron apps, test UI, take screenshots. Do NOT use for fetching or reading web content programmatically — use curl, MCP fetch tools, or domain-specific skills instead.
---

<strategy>
Read BROWSER-STRATEGY.md in this skill directory for the full decision framework. In short: Browser Use MCP (`mcp__browser-use__*`) is the primary tool for general browsing, scraping, and Electron apps. Chrome DevTools MCP (`mcp__chrome-devtools__*`) is for stealth on sites that detect automation (Google, banking, Cloudflare-protected).
</strategy>

<browser_use_workflow>
1. `mcp__browser-use__browser_navigate` - go to URL
2. `mcp__browser-use__browser_get_state` - see page elements with index refs
3. `mcp__browser-use__browser_click` / `mcp__browser-use__browser_type` - interact using index from state
4. `mcp__browser-use__browser_screenshot` - visual verification when needed
5. `mcp__browser-use__browser_close_all` - clean up when done
</browser_use_workflow>

<chrome_devtools_workflow>
Use only for sites that detect and block automated browsers (Google Workspace, banking, Cloudflare). Chrome Global must be running with remote debugging enabled before using these tools.

1. Ensure Chrome Global is running - `hypr-summon-chrome-global` (SUPER+C)
2. Ensure remote debugging is on - user must have toggled `chrome://inspect/#remote-debugging` and clicked Allow on the consent dialog (persists across restarts, only needed once)
3. `mcp__chrome-devtools__list_pages` - verify connection
4. `mcp__chrome-devtools__navigate_page` - go to URL
5. `mcp__chrome-devtools__take_snapshot` - see page elements with uid refs
6. `mcp__chrome-devtools__click` / `mcp__chrome-devtools__fill` - interact using uid from snapshot
7. `mcp__chrome-devtools__take_screenshot` - visual verification when needed
</chrome_devtools_workflow>

<connection_troubleshooting>
If Chrome DevTools MCP fails with "Could not connect to Chrome":

1. Verify Chrome Global is running: `hyprctl clients -j | jq '.[] | select(.class == "chrome-global")'`
2. If not running: `hypr-summon-chrome-global` (SUPER+C)
3. Check DevToolsActivePort exists: `cat ~/.config/chrome-global/DevToolsActivePort`
4. If no DevToolsActivePort: open `chrome://inspect/#remote-debugging` in Chrome Global and toggle it on, then click Allow on the consent dialog
</connection_troubleshooting>

<tips>
Browser Use: always get fresh state after navigation or interaction - element indices change. Prefer state over screenshots (less tokens).
Chrome DevTools: always take a fresh snapshot after navigation - uids change between snapshots. Prefer snapshots over screenshots.
</tips>
