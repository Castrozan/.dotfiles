---
description: GNOME keybinding debugging guidelines for NixOS with home-manager
alwaysApply: false
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

When custom keybindings don't work in GNOME on NixOS check dconf vs nix config sync. Run `dconf dump /org/gnome/settings-daemon/plugins/media-keys/` and compare with home/modules/gnome/dconf.nix. Custom keybinding slot numbers must match.

Check if keybinding is being grabbed. Run `killall gsd-media-keys` then `env -u GIO_EXTRA_MODULES /usr/libexec/gsd-media-keys 2>&1 &`. Watch for "Failed to grab accelerator" errors. This means something else holds the keybinding.

Common conflicts are GNOME Shell extensions like wsmatrix that have default keybindings overriding custom ones. Check extension schemas with `cat ~/.local/share/gnome-shell/extensions/*/schemas/*.xml | grep -i keybind`. Disable conflicting extension keybindings in dconf.nix.

Nix/system library conflicts show as "undefined symbol" or "Failed to load module" errors with Nix paths. The GIO_EXTRA_MODULES environment variable is polluted. Fix with `systemctl --user unset-environment GIO_EXTRA_MODULES` then `env -u GIO_EXTRA_MODULES /usr/libexec/gsd-media-keys &`.

Test keybindings with `dconf write /path/to/keybinding/command "'touch /tmp/test-file'"` then press keybinding and check if file was created with `ls /tmp/test-file`.

Wayland session restart required. Keybinding grabs persist in GNOME Shell on Wayland. After fixing conflicts user must log out and log back in for changes to take effect.

Key lesson: Always check GNOME Shell extension default keybindings when custom shortcuts fail. Extensions grab keys at a higher priority than gsd-media-keys custom keybindings.
