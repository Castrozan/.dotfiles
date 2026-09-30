<prebuilt_codex_distribution> Use upstream prebuilt release binaries for Codex and its code-mode host. Do not patch
upstream Codex or compile it from source; local source changes turn rebuilds and upgrades into expensive Rust builds.
Keep customization in supported configuration, hooks, and the launcher. </prebuilt_codex_distribution>

## Interactive sessions

The launcher selects embedded mode with `--no-daemon`, so each terminal owns its Codex process and environment. Package
upgrades apply to new launches without requiring existing terminals to close. Explicit remote connections retain their
native behavior; noninteractive commands and autonomous callers use the upstream launch path.

Native profiles carry interactive instructions and workspace overrides. Nix deploys their immutable sources separately
and seeds writable profile files during activation. Codex can save model and reasoning selections into those files;
rebuilds preserve those selections unless the workspace explicitly declares the corresponding setting. Instructions and
other workspace settings remain declarative. Malformed profile files fail activation without overwriting the file.
