---
name: browser
description: Interact with a live webpage inside a browser window — fill forms, click buttons, navigate authenticated apps, automate Electron apps, test web UI, capture browser-window screenshots for visual verification of web pages. Do NOT use for fetching or reading web content programmatically (use curl or MCP fetch). Do NOT use for desktop screenshots, system media/audio control, MPRIS players, or non-browser GUI — those belong to the desktop skill.
---

<strategy>
Two browser MCPs plus one CLI are available. Browser Use (`mcp__browser-use__*`) is the primary MCP - it launches its own Chrome, works immediately, handles general browsing and Electron apps. Chrome DevTools (`mcp__chrome-devtools__*`) connects to the user's real Chrome Global for stealth on sites that detect automation (Google, banking, Cloudflare). PinchTab (`pinchtab` CLI, no MCP) is the resilient fallback - its own persistent-profile Chrome (stays logged in across runs) driven entirely from bash; reach for it when the MCP transports are flaky or you need a stable already-authenticated session for a local app. Read docs/BROWSER-STRATEGY.md for the full decision framework.
</strategy>

<pinchtab_workflow>
CLI only (no MCP), driven from bash. Its server runs a persistent-profile Chrome on localhost:9867, so logins survive across runs (log in once in headed mode and stay authenticated). `pinchtab nav` auto-starts the local server.

1. `pinchtab nav <url>` - navigate (auto-starts the server; `--new-tab`, `--snap`)
2. `pinchtab snap` - accessibility tree with refs (prefer over screenshot)
3. `pinchtab screenshot --output <file>` - save a screenshot (then Read the file)
4. `pinchtab text` - extract page text; `pinchtab capture` - paired screenshot + snapshot from one DOM epoch
5. `pinchtab click <ref>` / `pinchtab type <ref> <text>` - interact using refs from `snap`
6. `pinchtab health` / `pinchtab tabs` - status; `pinchtab server -H` - headed (visible) for logging in
7. `pinchtab help` or `pinchtab <command> --help` for the full command and flag list

Guards are UP by default (allowed domains: localhost/127.0.0.1); `pinchtab server -y` lowers them. For an isolated tab set `PINCHTAB_SESSION=$(pinchtab session create --agent-id <id> --print-token)`.
</pinchtab_workflow>

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
1. Launch Chrome Global for the user: `hypr-summon-chrome-global` on Linux, `summon-chrome-global` on macOS
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
