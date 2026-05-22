---
name: vscode
description: Drive a real VS Code instance via the Chrome DevTools Protocol (CDP). Launch VS Code with `--remote-debugging-port`, then run high-level subcommands (open command palette, run a registered command by id, click DOM elements, capture screenshots, send messages to the Claude Code panel, read agent output). Use whenever a task needs VS Code automation — extension smoke tests, walking through a UI flow, validating that a new command shows up, or driving Claude Code-in-VS Code as a subordinate agent. Do NOT use for plain web browsing (use the `browser` skill) or for headless command-line VS Code operations covered by `code --install-extension` etc.
---

<canonical_invocation>
Every action goes through the dispatcher:

```
~/.dotfiles/agents/skills/vscode/scripts/vscode <verb> [args]
```

Never call `code --remote-debugging-port=...` directly — the dispatcher manages the CDP port, the user-data-dir, the PID file, and clean shutdown.
</canonical_invocation>

<lifecycle>
The Nix-wrapped `code` binary (see `~/.dotfiles/home/modules/editor/vscode/vscode.nix`) ALWAYS launches with:
- `--remote-debugging-port=9333` — exposes CDP on a fixed port
- `--remote-allow-origins=*` — required so CDP WebSocket handshakes succeed

These flags are injected by a `pkgs.symlinkJoin` + `wrapProgram` so they apply to every invocation of `code` system-wide — including when the user double-clicks the VS Code icon, runs `code` from a terminal, or this skill calls `code`. CDP is therefore always available against the user's real `~/.config/Code` profile (logged-in Claude Code sessions, extensions, settings all intact). The skill **never** writes a `--user-data-dir` flag and **never** touches `~/.config/Code` during `kill`.

1. `vscode launch [path]` — runs `code [path]` and waits for CDP. Reuses the existing instance if one is already on port 9333.
2. `vscode status` — show running instance pid + CDP pages.
3. `vscode kill` — `workbench.action.quit` then SIGTERM. Never touches the user-data-dir.
4. `vscode dismiss-modals [N]` — press Escape N times (default 3). Useful for stray notification balloons.
</lifecycle>

<ui_interaction>
- `vscode command-by-title <title>` — drive a VS Code command by typing its
  user-visible title into the Command Palette and pressing Enter. The argument
  is the **title** (e.g. `"Preferences: Open Settings (UI)"`, `"View: Show
  Betha Marketplace"`), NOT the internal command id like
  `workbench.action.openSettings`. Internal ids do not render in the palette
  unless an extension explicitly registers them. The title is also
  **locale-dependent**: a pt-BR install shows `"Preferências: Abrir
  Configurações (UI)"` and the en-US title will not match. CDP cannot reach
  the Extension Host, so there is no real `vscode.commands.executeCommand`
  bridge — this verb is the cheap "drive the UI" path. There is no way to
  pass command arguments.
- `vscode click <css-selector>` — DOM click for elements without a command
  (custom webview buttons, tree items, etc.).
- `vscode type <css-selector> <text>` — focus + type.
- `vscode screenshot [--out PATH] [--full]` — capture the VS Code window via
  CDP `Page.captureScreenshot`. `--full` captures the whole document, default
  is viewport.
</ui_interaction>

<agent_interaction>
Talk to the Claude Code chat panel as a subordinate agent. Despite the
"Build with Agent" framing the panel renders directly in the workbench DOM
(no separate WebView page), so we drive it with the same `.interactive-*`
selectors used by the workbench.

- `vscode agent send <message>` — focus the chat input, insert text, click
  send. Returns immediately after submit (does not wait for a reply).
- `vscode agent state` — `{running: bool, assistant_messages: N,
  send_disabled: bool}`. `running` is true iff a stop/cancel button is
  visible in the chat-execute-toolbar.
- `vscode agent read` — tail (last 2000 chars) of the most recent assistant
  message.
- `vscode agent wait-idle [--timeout SECS] [--poll SECS]` — block until the
  panel has been idle (no stop button, message count stable) across **3
  consecutive polls**. Defaults: timeout 1800s, poll 20s. Exit 2 on timeout.
  The 3-poll stability check is intentional: between sequential tool calls
  inside one assistant turn the stop button briefly disappears, so a single
  `running=false` poll would return prematurely.
- `vscode agent new | transcript | history` — stubs. Need separate selector
  pinning for the Sessions sidebar tree.

All implemented agent verbs use the same pinned selectors in
`scripts/_lib/cdp_cli.py` (`CHAT_*_SELECTOR`). If they break after a VS
Code or Claude Code update, run `vscode probe-chat-dom` and update
`docs/CDP-SELECTORS.md` + the constants.
</agent_interaction>

<betha_marketplace>
Sub-namespace for the Betha Marketplace lifecycle on a Linux ~/.config/Code
install. The verbs are filesystem + shell only (no CDP), but they live in
this skill because they manage VS Code state — the extension, the
agent-plugins federation cache, and the User/mcp.json that the sync engine
writes to.

- `vscode betha-marketplace wipe` — uninstalls
  `betha-sistemas.betha-marketplace-updater`, removes both prod and test
  federation caches under
  `~/.vscode/agent-plugins/gitlab.services.betha.cloud/betha-ai/`,
  strips `_betha_marketplace`-owned servers and inputs from
  `~/.config/Code/User/mcp.json` while preserving every user-added server
  and the `_betha_marketplace_overrides` block (the user-data escape
  hatch for per-host MCP overrides), and removes
  `installed.json` entries that point at the wiped federations.

- `vscode betha-marketplace install` — runs the prod `install.js`
  one-liner. Override the URL with `BETHA_MARKETPLACE_INSTALL_URL`. The
  one-liner clones `main` via SSH and installs the latest VSIX under
  `tools/vscode-extension/dist/` via `code --install-extension --force`.

- `vscode betha-marketplace status` — JSON snapshot:
  `extension_version`, `federation_version` (from
  `build-metadata.json`), `vsix_in_federation_cache` (the file
  `selfUpdate.ts` scans), `installed_plugin_count`,
  `owned_mcp_servers`, `user_overrides`.

- `vscode betha-marketplace verify` — pretty-prints status + exits
  non-zero if the extension or federation cache is absent. Emits a WARN
  (not FAIL) when the VSIX is missing from the cache, which silently
  breaks `selfUpdate.ts` — that file is only published by marketplace
  v2.8.2+ via the `copyLatestVscodeExtensionVsixIntoBundle` step in
  `src/core/marketplace-branch.ts`.

Typical zero-to-installed sequence:

```
vscode betha-marketplace wipe
vscode kill            # only needed when truly testing 'from zero'
vscode launch
vscode betha-marketplace install
vscode reload-window
vscode betha-marketplace verify
```

The wipe is safe to run while VS Code is open; the extension's
`watchInstalledJsonChanges` watcher will fire and re-sync.
`_betha_marketplace_overrides.<server>` survives because the sync engine
re-applies it whenever the matching server name appears again.
</betha_marketplace>

<tips>
- The CDP **page list** that matters is the renderer process page (`type: "page"`, URL starts with `vscode-file://`). The dispatcher filters automatically — but if you need raw access, `vscode cdp-pages --raw` dumps the JSON.
- `command-by-title` types into the Command Palette via simulated keyboard
  input. Internally it:
  1. Resolves a safe workbench-shell coordinate (`.menubar` rect → fallback
     to `.activitybar` bottom → fallback to `(10, 10)`) and clicks it to
     break focus out of any side panel that would intercept Ctrl+Shift+P.
  2. Press Escape to close any open dropdown/peek.
  3. Send Ctrl+Shift+P to open the palette.
  4. Insert the title text + press Enter.
  If your command doesn't run, screenshot first to see where the keystrokes
  actually landed.
- Always `screenshot` after a meaningful action when reporting back to the
  user — visual proof beats prose.
- Snapshots beat screenshots for analyzing structure (`vscode snapshot`
  returns the a11y tree of the active page).
- When VS Code's title bar shows "[Restricted Mode]", commands that touch
  the workspace are blocked. Use
  `vscode command-by-title "Manage Workspace Trust"` and click "Trust" in
  the dialog before continuing.
- Multiple VS Code instances on different ports: pass `--port N` to every command. Default port is 9333.
- To see the sidebar tree after a `View: Show ...` command, you may need a follow-up `workbench.action.toggleSidebarVisibility` if the sidebar was collapsed.
</tips>

<known_limitations>
- The Claude Code WebView DOM is undocumented — selectors are pinned in `docs/CDP-SELECTORS.md` and need refresh when Anthropic updates the extension. The dispatcher's `agent` verbs probe a few known selectors and fall back with a clear error.
- VS Code's main process and renderer share the same CDP endpoint; tools that target "the page" mean the renderer. Extension Host scripts are not reachable.
- Headless/SSH: requires X or a display. For pure CLI extension validation (install/uninstall), use `code --install-extension` directly, not this skill.
</known_limitations>

<security>
The Nix wrapper passes `--remote-debugging-port=9333 --remote-allow-origins=*` to every invocation of `code`. The implications:

- **Any local process can attach to CDP on port 9333.** Localhost-only — the
  port is not exposed externally — but any user-level process on this
  machine can drive the editor, including a malicious browser tab that
  bypasses CORS via a same-origin-spoofing trick (`--remote-allow-origins=*`
  defeats the origin gate). On a single-user workstation this is acceptable
  ergonomic risk; on a shared host it is not.
- **The driven editor loads the real user profile** (`~/.config/Code`),
  which carries logged-in sessions for Claude Code, GitHub Copilot, SSO
  cookies, and any other extension that persists credentials in its global
  state. An attacker who attaches to CDP can read those secrets, exfiltrate
  them via screenshot/snapshot, and impersonate the user inside any of
  those extensions.
- **`Input.insertText` and `Input.dispatchKeyEvent` reach the editor as if
  they were keystrokes.** An attacker can type and execute arbitrary
  terminal commands inside an open VS Code terminal pane.
- **Mitigation if the threat model changes**: drop `--remote-allow-origins=*`
  from `home/modules/editor/vscode/vscode.nix` (this breaks the skill's
  WebSocket attach until selectors-by-cookie or a port-knocking wrapper is
  added), or remove `--remote-debugging-port` entirely and launch a
  per-task instance with a randomized port + isolated user-data-dir.

Decision recorded 2026-05-19: accept the risk on this single-user
workstation. Revisit if the host becomes multi-user, or if a sandboxed
agent runs untrusted code against the same `~/.config/Code` profile.
</security>
