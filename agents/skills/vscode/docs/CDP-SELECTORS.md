# CDP Selectors Reference

Pinned CSS selectors and command IDs used by `scripts/_lib/cdp_cli.py`. Refresh
whenever VS Code or a critical extension bumps a major version and a verb stops
working.

## VS Code workbench (1.119)

| Region | Selector | Notes |
|---|---|---|
| Menu bar | top ~22 px of viewport (y ≤ 22) | Click to break focus out of side panels before sending Ctrl+Shift+P. |
| Command Palette input | `.quick-input-widget .input` | Receives `Input.insertText` after Ctrl+Shift+P. |
| Activity bar | `.activitybar` | Vertical icon column on the left. |
| Status bar | `.statusbar` | Bottom. |

## Useful built-in command IDs

| Action | Command ID |
|---|---|
| Reload window | `workbench.action.reloadWindow` |
| Quit | `workbench.action.quit` |
| Open Settings (UI) | `workbench.action.openSettings` |
| Toggle sidebar | `workbench.action.toggleSidebarVisibility` |
| Toggle auxiliary bar (Chat panel) | `workbench.action.toggleAuxiliaryBar` |
| Focus first editor group | `workbench.action.focusFirstEditorGroup` |
| Open Extensions view | `workbench.view.extensions` |
| Open Command Palette | `workbench.action.showCommands` |
| Trust workspace | `workbench.trust.manage` |

## Betha Marketplace extension (`betha-sistemas.betha-marketplace-updater@0.6.0`)

| Action | Command ID |
|---|---|
| Show sidebar | `View: Show Betha Marketplace` (palette title) or focus the `betha-marketplace` viewsContainer |
| Sync MCP servers | `betha.syncMcp` |
| Update marketplace cache | `betha.updateMarketplace` |
| Marketplace Doctor | `betha.marketplaceDoctor` |
| Refresh sidebar | `betha.refreshSidebar` |
| Install plugin (from tree item) | `betha.installPlugin` |
| Uninstall plugin (from tree item) | `betha.uninstallPlugin` |
| Install all plugins | `betha.installAllPlugins` |
| Edit credential | `betha.editCredential` |
| Open credentials.env | `betha.openCredentialsFile` |
| Add MCP server | `betha.addMcpServer` |
| Remove MCP server | `betha.removeMcpServer` |
| Check extension update | `betha.checkExtensionUpdate` |

## Claude Code chat panel (pinned 2026-05-19)

The chat panel renders directly in the workbench DOM (NOT in a separate
WebView page despite the "Build with Agent" UI). Selectors below are the
ones wired into `scripts/_lib/cdp_cli.py` as `CHAT_*_SELECTOR` constants.

| Element | Selector | Used by |
|---|---|---|
| Chat input editor (Monaco) | `.interactive-input-editor` | `agent send`: click center to focus, then `Input.insertText` |
| Send button | `.chat-execute-toolbar .action-label.codicon-arrow-up` | `agent send`: clicked after text inserted; has `.disabled` while input empty |
| Stop / cancel button | `.chat-execute-toolbar .action-label.codicon-stop-circle`, `.codicon-debug-stop`, `.codicon-stop` | `agent state`: visible iff a turn is in flight (running) |
| User request bubble | `.interactive-list .interactive-request` | not consumed (count available via probe) |
| Assistant response bubble | `.interactive-list .interactive-response` | `agent state` / `agent read`: count + tail text |
| IME helper textarea (sibling of Monaco) | `textarea.ime-text-area` inside `.interactive-input-editor > .chat-editor-container > .monaco-editor > .overflow-guard` | not directly used; keyboard events flow through CDP `Input.dispatchKeyEvent` instead |

Subverbs still using stubs (need additional pinning): `agent new`,
`agent transcript`, `agent history` — those need selectors for the
Sessions sidebar tree at the top of the chat pane.

### Refresh procedure (when selectors drift)

VS Code or Claude Code can ship a UI refresh that renames or restructures
these classes. To re-discover:

```
vscode launch ~/some-workspace
# open the chat panel in the running VS Code (Ctrl+L or run-command
# workbench.action.chat.openInSidebar)
vscode probe-chat-dom | jq
```

`probe-chat-dom` consolidates five earlier ad-hoc probes (probe-inputs,
probe-chat, probe-input-area, probe-chat-input, probe-messages). It
reports: which pinned selectors still resolve, candidate alternative
selectors for messages, every toolbar button with `aria-label`/disabled
state/rect, every editable element on the page, and the ancestor chain
of both the send button and the chat input. Diff the output against the
table above to identify what moved, then update the `CHAT_*_SELECTOR`
constants in `scripts/_lib/cdp_cli.py` and bump the date in this
section's heading.
