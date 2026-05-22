# shellcheck shell=bash
# Usage help. Sourced from `scripts/vscode`.

_print_usage_and_exit() {
	cat <<'USAGE'
vscode — drive VS Code via Chrome DevTools Protocol.

Usage:
  vscode [--port N] <verb> [args]

Lifecycle:
  launch [path]          run `code [path]` — the Nix-wrapped binary always
                         exposes CDP on port 9333 and uses your real
                         ~/.config/Code profile (logged-in Claude Code,
                         extensions, settings all intact).
  status                 show running instance + CDP pages
  kill                   close VS Code gracefully (never touches user-data-dir)
  wait-ready [--timeout SECS]
                         block until CDP responds on the port (default 30s).
                         Useful after a manual launch from a different shell.
  reload-window          send Developer: Reload Window via the palette and
                         block until the renderer is back on CDP. Locale-
                         tolerant: falls back to the pt-BR title if the
                         en-US one does not match.
  cdp-pages [--raw]      list CDP pages (use --raw for full JSON)
  probe-chat-dom         report the live DOM state of all pinned
                         Claude-Code chat selectors

UI:
  command-by-title <title>      type the user-visible command title into the
                                Command Palette and press Enter (locale-
                                dependent). No executeCommand bridge — CDP
                                cannot reach the Extension Host.
  click <selector>              CSS click on the active page
  type <selector> <text>        focus + type into a plain HTMLInputElement or
                                contenteditable surface
  type-focused <text>           send text via CDP Input.insertText to whatever
                                currently has focus. Required when the target
                                is a Monaco editor widget (Extensions sidebar
                                search, workbench Search input). Pair with a
                                preceding 'Focus on ... View' palette command.
  screenshot [--out PATH] [--full]   capture viewport (or whole document)
  snapshot                      a11y-tree snapshot of the active page

Agent (Claude Code panel — selectors pinned 2026-05-19 against VS Code 1.119):
  agent send <message>            click chat input, insert text, press send
  agent state                     {running: bool, assistant_messages: N}
  agent read                      latest assistant message text (tail 2000 chars)
  agent wait-idle [--timeout SECS] [--poll SECS]
                                  block until idle across 3 consecutive polls
                                  (default 1800s/20s)
  agent new | transcript | history    stubs — pending additional selector pinning

Betha Marketplace (betha-sistemas.betha-marketplace-updater + federation):
  betha-marketplace wipe          uninstall the extension, drop federation
                                  caches under ~/.vscode/agent-plugins, strip
                                  _betha_marketplace-owned servers/inputs from
                                  User/mcp.json (preserving user-added servers
                                  and _betha_marketplace_overrides), and remove
                                  installed.json entries pointing at the wiped
                                  federations.
  betha-marketplace install       run the install.js one-liner against the
                                  prod marketplace (override via env var
                                  BETHA_MARKETPLACE_INSTALL_URL).
  betha-marketplace trigger-clone [TIMEOUT_SECS]
                                  open the Extensions view, type @agentPlugins
                                  via CDP Input.insertText, wait for VS Code's
                                  chat.plugins.marketplaces federation system
                                  to clone the marketplace branch into the
                                  agent-plugins cache. Default timeout 90s.
                                  This is the canonical path (README Passo 5).
  betha-marketplace status        JSON snapshot of the current install state:
                                  extension_version, federation_version,
                                  vsix_in_federation_cache, installed_plugin_count,
                                  owned_mcp_servers, user_overrides.
  betha-marketplace verify        status + exit 0 only if extension installed
                                  and federation cache present. Warns (not
                                  fails) when the VSIX is missing from the
                                  cache, which would break selfUpdate.ts.

Global flags:
  --port N           CDP port (default 9333)

Examples:
  vscode launch ~/repo/ai-first-initiative
  vscode command-by-title "View: Show Betha Marketplace"
  vscode screenshot --out /tmp/sidebar.png
  vscode betha-marketplace wipe && vscode kill && vscode launch && \\
    vscode betha-marketplace install && vscode reload-window && \\
    vscode betha-marketplace trigger-clone && vscode betha-marketplace verify
USAGE
	exit 1
}
