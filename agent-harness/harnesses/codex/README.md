<prebuilt_codex_distribution>
Use upstream prebuilt release binaries for Codex and its code-mode host. Do not patch upstream Codex or compile it from
source; local source changes turn rebuilds and upgrades into expensive Rust builds. Keep customization in supported
configuration, hooks, and the launcher.
</prebuilt_codex_distribution>

## Shared interactive sessions

The launcher connects native terminals to one local app-server through one shared Python proxy. The proxy extends the
native JSON-RPC boundary because upstream shares the daemon's environment across clients. Each terminal registers its
environment and selected profile before the launcher replaces itself with the native CLI.

The proxy binds persistent thread replies to their terminal before forwarding them. Hooks resolve the native session ID
against an exclusive attachment lock, restore named pane variables, and deliver the selected developer instructions as
`SessionStart` context. This refreshes instructions on resume and compaction, where native developer-instruction overrides
alone did not refresh the model request. Ephemeral title threads receive no interactive binding. Context records contain
named session variables, selected instructions, and an environment fingerprint, rather than the full launch environment.

Shell tools receive their client's environment through the native shell policy, preserving exclusions and explicit
overrides. Configured stdio MCP servers receive client variables through their native environment configuration. Other
daemon children still inherit its startup environment; use `--no-daemon` for clients needing environment-based model or
HTTP MCP credentials.

One terminal owns each thread. A different terminal can resume it after the old attachment closes and its turn finishes.
An idle thread unloads immediately so its next resume can apply the new environment. A reconnect with the same launch
configuration may reuse a loaded thread. Unresolved or disconnected ownership never supplies a pane to hooks.

Nix selects the complete upstream package and disables its independent updater and remote control. Upgrades leave attached
clients running; a new launcher refuses to replace their proxy or daemon until those clients exit. Closing the last client
leaves an idle proxy and daemon. Their fixed memory cost can outweigh savings with few terminals. Native daemon crashes
recover on client reconnect; a proxy crash requires relaunching the terminals. A shared process failure affects every
attached terminal.

`codex --no-daemon` keeps the embedded launch path. Noninteractive commands and autonomous callers using the unwrapped
package retain their own launch behavior. No upstream source patch or synthetic initial conversation turn is required.

The native lifecycle contract is documented in the
[upstream daemon README](https://github.com/openai/codex/blob/main/codex-rs/app-server-daemon/README.md).
