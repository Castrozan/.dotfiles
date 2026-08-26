---
name: browser
description: Interact with live browser pages and Electron apps: navigate, fill forms, test UI, or capture browser-window screenshots. Not for programmatic fetching, desktop capture, media, or non-browser GUI.
---

<strategy>
Start every browser task with Chrome DevTools (`mcp__chrome-devtools__*`). It drives the user's real Chrome Global with
their live logins and no page-visible automation flags. When the user names Chrome DevTools, CDP, or the browser
harness, that choice is binding: stay on Chrome DevTools and never invoke, inspect, restart, or configure PinchTab. A
stale connection, zero attached pages, a blocking consent prompt, "Could not connect to Chrome," or another recoverable
tool error starts the recovery workflow below; none permits a tool switch. PinchTab is eligible only as the last resort
after Chrome DevTools remains unavailable after recovery, the user did not require Chrome DevTools, and an isolated
browser profile can satisfy the task. An autonomous clawde agent is mechanically denied the shared Chrome target; that
makes PinchTab eligible only for an unattended task that did not require Chrome DevTools. Otherwise report the blocked
Chrome DevTools requirement instead of silently substituting another browser. Read `pinchtab.md` only after every
eligibility condition holds. `README.md` explains the Chrome target's constraints.
</strategy>

<chrome_devtools_connection_and_recovery>
Connects to the user's real Chrome Global via `--autoConnect`. Chrome runs bare (no automation flags) so Google and
bot-detecting sites see a normal browser. The user must enable `chrome://inspect/#remote-debugging` once (persists
across restarts) and click Allow on the consent dialog once per Chrome session. If
`mcp__chrome-devtools__list_pages` returns no pages, reports a stale connection, or returns "Could not connect to
Chrome," recover in this order: 1) launch Chrome Global with `hypr-summon-chrome-global` on Linux or
`summon-chrome-global` on macOS; 2) tell the user to enable `chrome://inspect/#remote-debugging` if needed and click
Allow on the consent dialog; 3) call `mcp__chrome-devtools__list_pages` again. A dropped connection clears itself after
one failed tool call, and this retry reconnects. It blocks until the user clicks Allow, so call no other tools and do
not probe PinchTab while waiting.
</chrome_devtools_connection_and_recovery>

<chrome_devtools_operation>
Once connected, work in this order: 1) `mcp__chrome-devtools__list_pages` verifies the connection; 2)
`mcp__chrome-devtools__new_page` with `background: true` opens work in a fresh tab; never `navigate_page` the selected
tab because it replaces what the user has open. For profile-bound work, pick the account from the profile names in
`~/.config/chrome-global/Local State` and use that profile's open window; only when it has none, cold-start it with
`summon-chrome-work-profile` or `summon-chrome-personal-profile`; 3) `mcp__chrome-devtools__take_snapshot` returns uid
refs; 4) `mcp__chrome-devtools__click` and `mcp__chrome-devtools__fill` interact through a uid; 5)
`mcp__chrome-devtools__take_screenshot` captures visual evidence when needed.
</chrome_devtools_operation>

<tips>
Always take a fresh snapshot after navigation because uids change between snapshots. Prefer snapshots over screenshots.
The Chrome DevTools target is single and sequential and needs its own Allow.
</tips>

<knowledge>
For traps that cost real debugging: threads that virtualize their middle out of the DOM so a one-shot query silently
returns a partial read, pages that scroll inside a container rather than the window, and why an authenticated site needs
the real browser target; read `knowledge.md`.
</knowledge>
