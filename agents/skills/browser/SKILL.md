---
name: browser
description: Interact with a live webpage inside a browser window: fill forms, click buttons, navigate authenticated apps, automate Electron apps, test web UI, capture browser-window screenshots for visual verification of web pages. Do NOT use for fetching or reading web content programmatically (use curl or MCP fetch). Do NOT use for desktop screenshots, system media/audio control, MPRIS players, or non-browser GUI; those belong to the desktop skill.
---

<strategy>
Two browser paths: a stealth CDP target and the PinchTab CLI. Default to the stealth CDP target - it drives the user's
real everyday browser, carrying their live logins (Google SSO, Cloudflare Access, banking, anything already signed in)
and running bare so no page detects the automation, which is what most tasks need. Chrome DevTools
(`mcp__chrome-devtools__*`) attaches to the dedicated Chrome Global on every host. PinchTab (`pinchtab` CLI, no MCP) is
the deliberate fallback, never the reflex: its own persistent-profile Chrome driven from bash, holding none of the
user's real logins, for work you want isolated from the real browser (public scraping, bulk extraction, throwaway
browsing, Electron apps, local or dev sessions). One hard exception overrides the default: the stealth target is
reserved for the interactive session and exits without connecting when driven by an autonomous clawde agent, so
autonomous agents use PinchTab for everything. Read `README.md` for the full decision framework.
</strategy>

<chrome_devtools_workflow>
Connects to the user's real Chrome Global via `--autoConnect`. Chrome runs bare (no automation flags) so Google and
bot-detecting sites see a normal browser. The user must enable `chrome://inspect/#remote-debugging` once (persists
across restarts) and click Allow on the consent dialog once per Chrome session.

If `mcp__chrome-devtools__list_pages` returns "Could not connect to Chrome":
1. Launch Chrome Global for the user: `hypr-summon-chrome-global` on Linux, `summon-chrome-global` on macOS
2. Tell the user: "Enable chrome://inspect/#remote-debugging if not already on (persists across restarts). Then click
   Allow on the consent dialog that will appear when I connect."
3. Call `mcp__chrome-devtools__list_pages` - this call BLOCKS until the user clicks Allow on the consent dialog in
   Chrome. Do not call any other tools while waiting.

Once connected:
1. `mcp__chrome-devtools__list_pages` - verify connection
2. `mcp__chrome-devtools__new_page` with `background: true` - open work in a fresh tab; never `navigate_page` the
   currently selected tab, that replaces in place whatever the user has open there
3. `mcp__chrome-devtools__take_snapshot` - see page elements with uid refs
4. `mcp__chrome-devtools__click` / `mcp__chrome-devtools__fill` - interact using uid from snapshot
5. `mcp__chrome-devtools__take_screenshot` - visual verification when needed
</chrome_devtools_workflow>

<pinchtab_workflow>
CLI only (no MCP), driven from bash against a persistent-profile Chrome, so logins survive across runs (log in once,
stay authenticated). `pinchtab nav` auto-starts the local server. The config is reasserted declaratively on every
rebuild to full capability (evaluate, macro, screencast, download, cookies, network intercept, upload, clipboard, state
export all enabled; action guards and IDPI off), every host (`allowedDomains` and attach hosts wildcarded), and headed
by default, so commands just work with no manual `server -y`/`-H` or per-run guard lowering to remember.

1. `pinchtab nav <url>` - navigate (auto-starts the server; `--new-tab`, `--snap`)
2. `pinchtab snap` - accessibility tree with refs (prefer over screenshot)
3. `pinchtab screenshot --output <file>` - save a screenshot (then Read the file)
4. `pinchtab text` - extract page text; `pinchtab capture` - paired screenshot + snapshot from one DOM epoch
5. `pinchtab click <ref>` / `pinchtab type <ref> <text>` - interact using refs from `snap`
6. `pinchtab health` / `pinchtab tabs` - status; `pinchtab help` or `pinchtab <command> --help` for the full command and
   flag list

Display mode is one global setting on the single shared server, headed by default. Switch to no visible window with
`pinchtab-mode headless` and back with `pinchtab-mode headed`; bare `pinchtab-mode` prints the current mode. That
wrapper restarts the one server to apply, so the switch hits every client of it, and the next rebuild resets the resting
default to headed. There is no per-command or per-session headless flag: attempting an isolated second headless server
races the single control-server pidfile and comes up unhealthy, so switch the shared mode instead. After hand-editing
the config file, `pinchtab server restart` makes a running server pick it up.
</pinchtab_workflow>

<tips>
Chrome DevTools: always take a fresh snapshot after navigation - uids change between snapshots. Prefer snapshots over
screenshots. The target is single and sequential and needs its own Allow.
PinchTab: prefer `snap` (accessibility tree with refs) over screenshots for less tokens; get a fresh `snap` after
navigation or interaction because refs change.
</tips>
