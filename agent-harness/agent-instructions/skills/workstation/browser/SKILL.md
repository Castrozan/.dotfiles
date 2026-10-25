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
the user did not require Chrome DevTools, and an isolated browser profile can satisfy the task. Attaching to Chrome
Global can require scoped user approval for a new debugging connection. An unattended task without that approval uses
`start --headless` or an eligible OpenCLI workflow when the task permits it. Otherwise report the blocked Chrome
DevTools requirement instead of silently substituting another browser.

Read [OpenCLI](references/opencli.md) for site commands and eligible isolated workflows.
[chrome target](references/chrome-target.md) explains the Chrome target's constraints.

Use OpenCLI site adapters for repeatable site reads when an isolated profile meets the request; this does not broaden
eligibility for generic browser fallback. Read [OpenCLI](references/opencli.md) for job ownership and adapter
development.

### Worker ownership

Read `chrome-devtools --help` and each command's help for syntax. The plugin also carries the executable at
`native/browser/chrome-devtools`. Default startup attaches to Chrome Global. Reuse the current task's authorized worker
before starting another. Prefer `start --headless` when existing logins, open tabs, and visible interaction are
unnecessary; headless does not inherit the user's current logins. Never borrow another task's worker or change its
ownership identifier.

Keep one worker for a browser task and run `stop` when finished. The completion hook also closes workers owned by the
current Herdr pane or Codex thread; outside those contexts, explicit `stop` is required. A fresh worker discards page
IDs and snapshot refs, so enumerate pages and take a fresh snapshot before continuing an earlier task.

CLI tool failures can print `Error:` while exiting successfully. Read the tool output and verify the resulting browser
state instead of treating exit status alone as success.

### Chrome devtools connection and recovery

Use the managed `connect` command to verify a task-owned connection within a deadline; read `connect --help` first. Keep
the worker across task steps. Its existing authorized CDP transport avoids repeated grants; a running worker alone does
not prove Chrome is still attached. A new connection can require Allow again, including after cleanup. Chrome's remote
debugging setting remains user-controlled; do not change settings or launch flags to suppress consent.

When a new grant is needed, prepare the exact Chrome target and obtain explicit user approval for that connection before
consuming its one-use token. A standing preference for automation is not approval for future access grants. The native
helper starts before the potentially blocking request, handles only the matching fresh Chrome consent dialog, then
exits. Unsupported layouts, stale prompts, ambiguity, or user input abort the attempt; use manual scoped approval in
those cases. Read [connection consent](references/connection-consent.md) before using native approval.

Run connection attempts through an execution tool that yields promptly, retaining its process handle so the agent can
continue independent work while consent is pending. Do not synchronously block the agent on `list_pages`, retry in a
loop, or start parallel attached clients. The wrapper rejects overlapping attached operations. On failure it cancels the
request and cleans only its own worker; inspect any cleanup error before retrying.

If Chrome is absent, summon Chrome Global through the platform's existing launcher. If debugging is disabled, ask the
user to enable it. After a stale connection or empty page list, inspect the failure and use one scoped reconnect. Keep
an explicit Chrome DevTools requirement throughout recovery; none of these failures permits probing OpenCLI.

### Chrome devtools operation

Once connected, work in this order: 1) `connect` verifies the connection; 2) `new_page` with `--background true` opens
work in a fresh tab; never `navigate_page` the selected tab because it replaces what the user has open.

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
