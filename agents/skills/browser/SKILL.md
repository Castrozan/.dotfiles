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
Use only for sites that detect and block automated browsers (Google Workspace, banking, Cloudflare).

1. Ensure Chrome Global is running - run `hypr-summon-chrome-global`
2. `mcp__chrome-devtools__list_pages` - verify connection
3. `mcp__chrome-devtools__navigate_page` - go to URL
4. `mcp__chrome-devtools__take_snapshot` - see page elements with uid refs
5. `mcp__chrome-devtools__click` / `mcp__chrome-devtools__fill` - interact using uid from snapshot
6. `mcp__chrome-devtools__take_screenshot` - visual verification when needed
</chrome_devtools_workflow>

<connection_troubleshooting>
If Chrome DevTools MCP fails with "Could not connect to Chrome":

1. Verify Chrome Global is running: `hyprctl clients -j | jq '.[] | select(.class == "chrome-global")'`
2. Check DevToolsActivePort exists: `cat ~/.config/chrome-global/DevToolsActivePort`
3. If no DevToolsActivePort, Chrome was launched without --remote-debugging-port=0. Use SUPER+C (summon script) to relaunch.
</connection_troubleshooting>

<tips>
Browser Use: always get fresh state after navigation or interaction - element indices change. Prefer state over screenshots (less tokens).
Chrome DevTools: always take a fresh snapshot after navigation - uids change between snapshots. Prefer snapshots over screenshots.
</tips>
