<prebuilt_codex_distribution> Use upstream prebuilt release binaries for Codex and its code-mode host. Do not patch
upstream Codex or compile it from source; local source changes turn rebuilds and upgrades into expensive Rust builds.
Keep customization in supported configuration, hooks, and the launcher. </prebuilt_codex_distribution>

## Interactive sessions

The launcher starts a private app-server on a Unix socket for each interactive terminal and stops it when the terminal
client exits. Package upgrades apply to new launches without requiring existing terminals to close. Explicit remote
connections and `--no-daemon` retain their native behavior; noninteractive commands and autonomous callers use the
upstream launch path.

After the first prompt creates the session, SessionStart derives its Servant from the thread ID and sets the native
thread name through that terminal's server. The footer displays the name. Existing titles retain their text with the
Servant prefixed in brackets; resume and compaction keep the same identity, while forks derive one from their new ID.

Native profiles carry interactive instructions and workspace overrides. Nix deploys their immutable sources separately
and seeds writable profile files during activation. Codex can save model and reasoning selections into those files;
rebuilds preserve those selections unless the workspace explicitly declares the corresponding setting. Instructions and
other workspace settings remain declarative. Profiles reuse the main configuration's merge policy for project trust,
marketplaces, plugins, and hook approvals. Malformed profile files fail activation without overwriting the file.
