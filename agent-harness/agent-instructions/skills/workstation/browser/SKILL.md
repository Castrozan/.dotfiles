---
name: browser
description: "Control browser pages and Electron apps through Chrome DevTools CLI or eligible OpenCLI workflows. Not for desktop capture, media, or other GUI."
---

### Strategy

Use the managed `chrome-devtools` CLI for interactive browser tasks. It attaches to Chrome Global with the user's
existing logins. When the user names Chrome DevTools, CDP, or the browser harness, that choice is binding: stay on
Chrome DevTools and never invoke, inspect, restart, or configure OpenCLI. A stale connection, zero attached pages, a
blocking consent prompt, "Could not connect to Chrome," or another recoverable tool error starts the recovery workflow
below; none permits a tool switch.

OpenCLI is eligible only as the last resort when every recovery step has failed, Chrome DevTools remains unavailable,
the user did not require Chrome DevTools, and an isolated browser profile can satisfy the task. An autonomous clawde
agent is mechanically denied the shared Chrome target; that makes OpenCLI eligible only for an unattended task that did
not require Chrome DevTools. Otherwise report the blocked Chrome DevTools requirement instead of silently substituting
another browser.

Read [OpenCLI](references/opencli.md) for site commands and eligible isolated workflows.
[chrome target](references/chrome-target.md) explains the Chrome target's constraints.

Use OpenCLI site adapters for repeatable site reads when an isolated profile meets the request; this does not broaden
eligibility for generic browser fallback. Read [OpenCLI](references/opencli.md) for job ownership and adapter
development.

### Worker ownership

Read `chrome-devtools --help` and each command's help for syntax. The plugin also carries the executable at
`native/browser/chrome-devtools`. Default startup attaches to Chrome Global; choose `start --headless` explicitly for
work that can use a separate profile. Headless does not inherit the user's current logins.

Keep one worker for a browser task and run `stop` when finished. The completion hook also closes workers owned by the
current Herdr pane or Codex thread; outside those contexts, explicit `stop` is required. A fresh worker discards page
IDs and snapshot refs, so enumerate pages and take a fresh snapshot before continuing an earlier task.

CLI tool failures can print `Error:` while exiting successfully. Read the tool output and verify the resulting browser
state instead of treating exit status alone as success.

### Chrome devtools connection and recovery

Connects to the user's real Chrome Global via `--autoConnect`, preserving its normal launch flags. The user must enable
`chrome://inspect/#remote-debugging` once (persists across restarts). A new attached connection can require the user to
click Allow again, including after worker cleanup.

If attached `chrome-devtools list_pages` returns no pages, reports a stale connection, or returns "Could not connect to
Chrome," recover in this order: 1) launch Chrome Global with `hypr-summon-chrome-global` on Linux or
`summon-chrome-global` on macOS; 2) tell the user to enable `chrome://inspect/#remote-debugging` if needed and click
Allow on the consent dialog; 3) call `chrome-devtools list_pages` again. A dropped connection clears itself after one
failed tool call, and this retry reconnects. It blocks until the user clicks Allow, so call no other tools and do not
probe OpenCLI while waiting.

### Chrome devtools operation

Once connected, work in this order: 1) `list_pages` verifies the connection; 2) `new_page` with `--background true`
opens work in a fresh tab; never `navigate_page` the selected tab because it replaces what the user has open.

For profile-bound work, pick the account from the profile names in `~/.config/chrome-global/Local State` and use that
profile's open window; only when it has none, cold-start it with `summon-chrome-work-profile` or
`summon-chrome-personal-profile`; 3) `take_snapshot` returns uid refs; 4) `click` and `fill` interact through a uid; 5)
save `take_screenshot` to a file and inspect it with the image viewer.

### Tips

Always take a fresh snapshot after navigation because uids change between snapshots. Prefer snapshots over screenshots.
The Chrome DevTools target is single and sequential and needs its own Allow.

Start attached recording only after bringing the owned target tab forward; background tabs can wait indefinitely for
their first frame. Headless recording needs no desktop focus. Stop recording before stopping its worker.

In headless mode, activate an owned background tab with `select_page --bringToFront true` before input or recording.
Background rendering throttling can otherwise make input time out; activation inside headless Chrome shows no window.

### Knowledge

For traps that cost real debugging: threads that virtualize their middle out of the DOM so a one-shot query silently
returns a partial read, pages that scroll inside a container rather than the window, and why an authenticated site needs
the real browser target; read [knowledge](references/knowledge.md).
