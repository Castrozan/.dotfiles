# Context Mode trial

Run `claude-context-mode` from a real project to start the normal interactive Claude launcher with the pinned
Context Mode plugin. Existing Claude settings, authentication, workspace profiles and hooks still apply. Ordinary
`claude` launches do not load this trial.

The plugin adds its MCP tools and all six upstream hooks: automatic tool routing, event capture, user decisions,
compaction snapshots, session restoration and turn completion. Run `/context-mode:ctx-stats` during work to inspect
the plugin's recorded tool-output reduction. Those figures do not establish billing savings or task quality.

The runtime uses Bun's SQLite support. Nix installs locked dependencies without npm lifecycle scripts and loads the
plugin with Claude's `--plugin-dir` option. Only the plugin manifest and hook commands receive local launch wiring;
upstream hook and server implementations remain unchanged. The MCP server starts through the bundled CLI instead of
the marketplace cache bootstrap, because Nix owns the immutable installation.

The plugin's processes use `${XDG_STATE_HOME:-$HOME/.local/state}/context-mode` for their databases, private config
and logs. Claude itself keeps its usual configuration root. No marketplace registration or global settings merge is
needed. The plugin has the user's normal filesystem and network access; its execution sandbox is a subprocess,
not an operating-system security boundary. Captured project content stays on disk in that state directory.

The private plugin config contains an empty settings file because upstream doctor requires that file before checking
plugin-declared hooks. It declares no hooks or user preferences; Claude loads the hooks from the plugin itself.

Upgrade the dependency pin and lock through Nix, then rebuild; `/context-mode:ctx-upgrade` cannot update this
immutable installation. Hosted Insight is not configured by this module.

To stop using the trial immediately, exit that Claude session and launch `claude`. To uninstall it, remove the
`./context-mode` import from the parent Claude module and rebuild. This removes both commands and the plugin link.
Existing Claude configuration requires no rollback. Delete the dedicated state directory separately if its retained
project data is no longer needed.

Upstream: `https://github.com/mksglu/context-mode`

Claude plugin loading: `https://code.claude.com/docs/en/plugins-reference`
