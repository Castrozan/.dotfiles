# Impasto desktop shell

chise runs [Impasto](https://github.com/andreumassanet/impasto) (GPL-3.0, by Andreu Massanet) from the fork
[Castrozan/impasto](https://github.com/Castrozan/impasto), pinned as the `impasto` flake input. The fork carries what
upstream's Arch installer cannot give NixOS: a flake package, classic hyprlang dispatches beside the Lua ones, the
`bar pin` command and the `IMPASTO_LOCK_COMMAND` hand-off to hyprlock. It also carries the pieces of the previous bar
Impasto lacked: GPU stats, the VPN and keyboard backlight modules and the Bluetooth audio profile picker.

## Going back to the previous shell

Set `custom.desktopShell.active = "quickshell-bar";` in `machine-configuration/machines/chise/home/desktop-shell.nix`
and run `rebuild`. That one option restores the Caelestia-based bar, mako and their four key bindings, and removes the
Impasto unit. The previous shell's code stays in `../bar` until Lucas says Impasto is good.

## What the selector moves

`custom.desktopShell.active` decides which shell module contributes the unit list in
`~/.config/hypr-shell/autostart.conf` and the bindings in `~/.config/hypr-shell/bindings.conf`.
Impasto owns notifications, so mako exists only with the
previous shell. The overview and window switcher are separate services and run with either shell.

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
