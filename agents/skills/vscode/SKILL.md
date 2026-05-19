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
VS Code is launched in an **isolated** user-data-dir under `/tmp/vscode-cdp-<port>` so it cannot pollute Lucas's main profile. Extensions still come from the host extension dir (`~/.vscode/extensions`) so the betha-marketplace-updater + agent plugins are present, but settings, workspace state, and chat history live in the temp dir.

Launch flags applied automatically:
- `--remote-debugging-port=<port>` + `--remote-allow-origins=*` — exposes CDP over WebSocket
- `--user-data-dir=/tmp/vscode-cdp-<port>` — isolated profile
- `--new-window` — never attach to an existing window
- `--disable-extension=GitHub.copilot-chat` + `--disable-extension=GitHub.copilot` — Copilot Chat auto-focuses the auxiliary side bar input and swallows palette keychords. Pass `--keep-copilot` to opt back in.

Pre-seeded `User/settings.json` disables: welcome page, tips, telemetry, workspace-trust prompt, auxiliary activity bar, secondary side bar, chat command center. Re-run `launch` after deleting the user-data-dir to refresh the seed.

1. `vscode launch [path] [--disable-extension ID] [--keep-copilot]` — start the instance. Reuses the existing one if already running on the same port. Returns the CDP page list.
2. `vscode status` — show running instance, CDP pages, websocket URL.
3. `vscode kill` — close gracefully (`workbench.action.quit`), then SIGTERM the process, then `rm -rf` the user-data-dir.
4. `vscode dismiss-modals [N]` — press Escape N times (default 3). Useful when a sign-in modal or notification balloon is up.
</lifecycle>

<ui_interaction>
- `vscode run-command <command-id> [arg-json]` — execute a registered VS Code command. The reliable way to drive the editor (avoids brittle DOM clicks). Examples: `betha.syncMcp`, `workbench.action.reloadWindow`, `workbench.view.extensions`, `workbench.action.openSettings`.
- `vscode palette <query>` — open Command Palette, type the query, press Enter on the first match. Use only when you need fuzzy matching; prefer `run-command` with the exact id when known.
- `vscode click <css-selector>` — DOM click for elements without a command (custom webview buttons, tree items, etc.).
- `vscode type <css-selector> <text>` — focus + type.
- `vscode screenshot [--out PATH] [--full]` — capture the VS Code window via CDP `Page.captureScreenshot`. `--full` captures the whole document, default is viewport.
</ui_interaction>

<agent_interaction>
Talk to the Claude Code panel inside VS Code as a subordinate agent. The panel is a WebView under VS Code's window; the dispatcher finds it by URL pattern (`vscode-webview://*claude-code*`).

- `vscode agent new` — start a new conversation in the active workspace.
- `vscode agent send <message>` — type a message into the input box and submit.
- `vscode agent read [--since N]` — return the latest N assistant messages (default: all since last `read`).
- `vscode agent transcript [--session-id ID]` — full transcript for the active or named session.
- `vscode agent history` — list past sessions in the current workspace.

These are **higher level than `run-command`** — they coordinate multiple CDP calls (find the right WebView, focus the input, type, click send, poll for new content). Implementation detail lives in `scripts/_lib/agent.py`.

Selectors for the WebView DOM are documented in `docs/CDP-SELECTORS.md` and pinned per Claude Code extension version because Anthropic ships UI updates.
</agent_interaction>

<tips>
- The CDP **page list** that matters is the renderer process page (`type: "page"`, URL starts with `vscode-file://`). The dispatcher filters automatically — but if you need raw access, `vscode cdp-pages --raw` dumps the JSON.
- `run-command` and `palette` both type into the Command Palette via simulated keyboard input. Internally they:
  1. Click the menu bar (x=400, y=8) to break focus out of any side panel.
  2. Press Escape to close any open dropdown/peek.
  3. Send Ctrl+Shift+P to open the palette.
  4. Insert the query text + press Enter.
  If your command doesn't run, screenshot first to see where the keystrokes actually landed.
- `run-command` is the cheapest way to drive the editor. Reach for `palette` only when you need fuzzy matching and don't know the id.
- Always `screenshot` after a meaningful action when reporting back to the user — visual proof beats prose.
- Snapshots beat screenshots for analyzing structure (`vscode snapshot` returns the a11y tree of the active page).
- When VS Code's title bar shows "[Restricted Mode]", commands that touch the workspace are blocked. Use `vscode run-command workbench.trust.manage` and click "Trust" in the dialog (or run `workbench.action.trustCurrentFolder`) before continuing.
- Multiple VS Code instances on different ports: pass `--port N` to every command. Default port is 9333.
- To see the sidebar tree after a `View: Show ...` command, you may need a follow-up `workbench.action.toggleSidebarVisibility` if the sidebar was collapsed.
</tips>

<known_limitations>
- The Claude Code WebView DOM is undocumented — selectors are pinned in `docs/CDP-SELECTORS.md` and need refresh when Anthropic updates the extension. The dispatcher's `agent` verbs probe a few known selectors and fall back with a clear error.
- VS Code's main process and renderer share the same CDP endpoint; tools that target "the page" mean the renderer. Extension Host scripts are not reachable.
- Headless/SSH: requires X or a display. For pure CLI extension validation (install/uninstall), use `code --install-extension` directly, not this skill.
</known_limitations>
