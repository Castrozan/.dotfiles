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

## Claude Code WebView (PINNING REQUIRED)

The Claude Code panel in VS Code is a WebView. Its DOM is undocumented and
selectors are NOT yet pinned. To complete the `vscode agent send|read|...`
verbs, follow this procedure:

1. `vscode launch --keep-copilot` (or whatever your Claude Code distribution
   requires — Copilot is disabled by default).
2. Open the Claude Code panel manually in the running VS Code window.
3. `vscode cdp-pages --raw` and locate the page with URL containing
   `vscode-webview://*claude-code*`.
4. `vscode snapshot > /tmp/claude-code-snapshot.json`.
5. Inspect for the input box (likely a `textarea` or `[contenteditable]`),
   the send button (likely an `aria-label` like "Send Message"), and the
   message-list container.
6. Pin the selectors below and update `dispatch_agent_subverb` to use them.

| Element | Selector | Verified |
|---|---|---|
| Input box | TBD | ❌ |
| Send button | TBD | ❌ |
| Message list root | TBD | ❌ |
| Assistant message bubble | TBD | ❌ |
| New conversation button | TBD | ❌ |
| Session history button | TBD | ❌ |
