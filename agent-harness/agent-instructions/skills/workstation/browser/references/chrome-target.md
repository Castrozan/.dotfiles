### Tool selection

`SKILL.md` owns browser-tool selection: Chrome DevTools first, explicit user tool choice binding, and OpenCLI eligible
only as its defined last resort. This file explains why the Chrome target has consent, concurrency, and tab-safety
constraints; it does not broaden fallback eligibility.

### Stealth cdp target chrome global

The attached target is the managed `chrome-devtools` CLI pointed at the Chrome Global user-data directory
(`~/.config/chrome-global`), which can contain multiple account profiles with separate cookies, logins, and extensions.
Prefer it when the task needs the user's actual everyday accounts or hits a bot-detecting site (Google, banking,
anything behind Cloudflare or PerimeterX). It is the user's real logged-in session, so treat it as the user's own and
never clobber the open tab.

### Profile selection

Match the required account to the profile names in `~/.config/chrome-global/Local State`. Use the desktop skill's native
browser interaction to select that profile's existing window and open a fresh task tab there. On macOS, Chrome's
AppleScript interface can create the tab in a specific window. If the profile has no window, use its declared launcher,
`summon-chrome-work-profile` or `summon-chrome-personal-profile`.

Return to DevTools: enumerate pages, identify the tab just created, take its snapshot, and verify the signed-in account
before editing. `new_page` can create a tab in a different profile even when the desired profile is visible. The consent
prompt's window does not identify the profile of every accessible tab; verify the account on the task tab itself. Keep
site interactions on DevTools when the user requires it; native profile selection does not change that choice.

### Chrome devtools is stealth by consent

The attached worker connects via `--autoConnect` to the user's normally launched Chrome and retains its profile,
cookies, logins and extensions. Each new session raises Chrome's Allow prompt; do not replace it with an always-on
debugging port or automation launch flags on the user's browser.

### Chrome devtools consent ownership

Reuse the current task's worker for its lifetime; reconnecting creates another grant boundary. Chrome's supported
`--autoConnect` flow requests permission for each new session. Do not expose a debugging port, change settings, or
retain workers across unrelated tasks to avoid that boundary. See [connection consent](connection-consent.md).

Serialize connection consent and commands within each worker. Separate workers can operate concurrently on their own
tabs. Connection verification has a deadline and runs detached from the agent's tool call. The bounded helper must be
ready before the DevTools call that can wait on Allow; starting it afterwards can leave the agent unable to act. A
timeout cancels this attempt and cleans its worker rather than retrying consent.

### Real browser never clobber the users open tab

The CDP target attaches to a real browser whose selected page on connect is the user's live foreground tab.
`navigate_page` replaces that tab's content in place instead of opening a new one. Navigating the selected tab therefore
silently destroys whatever the user had open there. Open a fresh task tab with `new_page` and `background: true` or
through [profile selection](#profile-selection), or `select_page` onto a tab you already own; reserve `navigate_page`
for a tab you opened yourself. This is intended chrome-devtools-mcp behavior through the latest release, not a bug a
version bump fixes, so do not chase a newer pin for it.

### Worker lifetime and performance

The CLI uses an MCP worker internally while a task is active. Stopping that worker disconnects attached Chrome and
closes a worker-launched headless browser. It does not close the user's regular Chrome. Keep the connection across steps
within a task, then stop it; reconnecting for every command adds startup and consent overhead.

Measure complete workflows and separate cold startup, warm commands, rendering waits and active memory. Headless removes
desktop interruptions but still runs Chrome's rendering engine. Native background throttling can delay an attached tab's
rendering or recording until the tab is visible.

### OpenCLI tradeoffs

OpenCLI runs a separate persistent-profile Chrome with none of the user's real-browser logins. It can satisfy eligible
isolated work after Chrome DevTools recovery fails. It cannot substitute for an explicitly requested Chrome DevTools
session or authenticated work that depends on the real profile. `SKILL.md` owns the last-resort gate;
[OpenCLI](opencli.md) owns the workflow after that gate passes.
