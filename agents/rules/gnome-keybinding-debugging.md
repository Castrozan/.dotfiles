---
description: GNOME keybinding debugging guidelines for NixOS with home-manager
alwaysApply: false
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<dconf_sync>
When custom keybindings don't work: check dconf vs nix config sync. Run dconf dump /org/gnome/settings-daemon/plugins/media-keys/ and compare with home/modules/gnome/dconf.nix. Custom keybinding slot numbers must match.
</dconf_sync>

<grab_check>
Check if keybinding is being grabbed: killall gsd-media-keys then env -u GIO_EXTRA_MODULES /usr/libexec/gsd-media-keys 2>&1 &. Watch for "Failed to grab accelerator" errors - means something else holds the keybinding.
</grab_check>

<extension_conflicts>
Common conflicts: GNOME Shell extensions like wsmatrix have default keybindings overriding custom ones. Check extension schemas: cat ~/.local/share/gnome-shell/extensions/*/schemas/*.xml | grep -i keybind. Disable conflicting extension keybindings in dconf.nix.
</extension_conflicts>

<library_conflicts>
Nix/system library conflicts show as "undefined symbol" or "Failed to load module" errors with Nix paths. GIO_EXTRA_MODULES environment variable is polluted. Fix: systemctl --user unset-environment GIO_EXTRA_MODULES then env -u GIO_EXTRA_MODULES /usr/libexec/gsd-media-keys &.
</library_conflicts>

<testing>
Test keybindings: dconf write /path/to/keybinding/command "'touch /tmp/test-file'" then press keybinding, check ls /tmp/test-file.
</testing>

<session_restart>
Wayland session restart required. Keybinding grabs persist in GNOME Shell on Wayland. After fixing conflicts: user must log out and log back in.
</session_restart>

<key_lesson>
Always check GNOME Shell extension default keybindings when custom shortcuts fail. Extensions grab keys at higher priority than gsd-media-keys custom keybindings.
</key_lesson>
