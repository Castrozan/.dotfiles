### Tool selection

`SKILL.md` owns browser-tool selection: Chrome DevTools first, explicit user tool choice binding, and OpenCLI eligible
only as its defined last resort. This file explains why the Chrome target has consent, concurrency, and tab-safety
constraints; it does not broaden fallback eligibility.

### Stealth cdp target chrome global

The attached target is the managed `chrome-devtools` CLI pointed at the dedicated Chrome Global profile
(`~/.config/chrome-global`) on every host, carrying that browser's own cookies, logins, and extensions. Prefer it when
the task needs the user's actual everyday accounts or hits a bot-detecting site (Google, banking, anything behind
Cloudflare or PerimeterX); it is the user's real logged-in session, so treat it as the user's own and never clobber the
open tab.

### Chrome devtools is stealth by consent

The attached worker connects via `--autoConnect` to the user's normally launched Chrome and retains its profile,
cookies, logins and extensions. Consent lives in the user's manual Allow on `chrome://inspect`; do not replace that gate
with an always-on debugging port or automation launch flags on the user's browser.

### Chrome devtools never break the gate

Three traps each waste a whole session if hit: 1) the first `list_pages` after a new attached connection can BLOCK until
the user clicks Allow, which is expected and not a hang, so wait for it and never time it out, retry-storm it, kill the
process, or report it broken;

2\) never add `--remote-debugging-port` or any automation flag to suppress the prompt, that flag is exactly what
destroys the stealth and the recurring manual Allow is the cost of invisibility by design;

3\) the target is one browser, single and sequential, so never drive it from parallel agents or open concurrent clients
because each new client needs its own Allow and they can wait while the browser serializes them. Work through one agent
and one attached connection at a time.

### Real browser never clobber the users open tab

The CDP target attaches to a real browser whose selected page on connect is the user's live foreground tab, and
`navigate_page` replaces that tab's content in place instead of opening a new one, so navigating the selected tab
silently destroys whatever the user had open there. Always open work with `new_page` and `background: true`, which loads
a fresh tab without stealing the user's focus, or `select_page` onto a tab you already own; reserve `navigate_page` for
a tab you opened yourself. This is intended chrome-devtools-mcp behavior through the latest release, not a bug a version
bump fixes, so do not chase a newer pin for it.

### Worker lifetime and performance

The CLI uses an MCP worker internally while a task is active. Stopping that worker disconnects attached Chrome and
closes a worker-launched headless browser. It does not close the user's regular Chrome. Keep the connection across steps
within a task, then stop it; reconnecting for every command adds startup and consent overhead.

Measure complete workflows and separate cold startup, warm commands, rendering waits and active memory. Headless removes
desktop interruptions but still runs Chrome's rendering engine. Native background throttling can delay an attached tab's
rendering or recording until the tab is visible.

### OpenCLI tradeoffs

OpenCLI runs a separate persistent-profile Chrome with none of the user's real-browser logins. It can satisfy eligible
isolated work after Chrome DevTools recovery fails, but it cannot substitute for an explicitly requested Chrome DevTools
session or authenticated work that depends on the real profile. `SKILL.md` owns the last-resort gate;
[OpenCLI](opencli.md) owns the workflow after that gate passes.
