# Impasto desktop shell

chise runs [Impasto](https://github.com/andreumassanet/impasto) (GPL-3.0, by Andreu Massanet) from the fork
[Castrozan/impasto](https://github.com/Castrozan/impasto), pinned as the `impasto` flake input. The fork carries what
upstream's Arch installer cannot give NixOS: a flake package, classic hyprlang dispatches beside the Lua ones, the
`bar pin` command and the `IMPASTO_LOCK_COMMAND` hand-off to hyprlock. It also carries the pieces of the previous bar
Impasto lacked: GPU stats, the VPN and keyboard backlight modules and the Bluetooth audio profile picker.

## The previous shell

The previous bar and mako were removed; git history holds them.

## What the module writes

The module starts its unit from `~/.config/hypr-shell/autostart.conf` and binds its keys in
`~/.config/hypr-shell/bindings.conf`, both sourced by `hyprland.conf`. Impasto owns notifications, so no other
notification daemon runs. The overview and window switcher are separate services.

## State and first run

Impasto keeps its settings in `~/.local/state/quickshell/settings.json`, which stays writable so its Settings window
works. Activation seeds that file once when it is missing: bar and dock hidden until pointed at, and no palette pushed
to other programs, because the hypr-theme pipeline owns those. A machine adds its own values, such as the VPN unit,
through `custom.desktopShell.impastoFirstRunSettings`. Delete the file and rebuild to get the seed again; a seed change
never reaches a settings file that already exists.

The fork's `settingsScale` setting enlarges the Settings window alone, leaving the bar, island and dock at their own
size; chise seeds 1.25, and Settings › Appearance › Type changes it.

## Working on the fork

Clone the fork, commit, push, then pin the new revision in `repository/flake-assembly/dependencies/flake.nix` and run
`nix flake update dependencies/impasto`. Call the running shell with `impasto-shell ipc --any-display call TARGET
FUNCTION`; `impasto-shell ipc --any-display show` lists every target. [MIGRATION.md](MIGRATION.md) lists every feature
of the previous bar with where it went.
