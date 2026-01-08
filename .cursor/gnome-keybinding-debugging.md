---
description: GNOME keybinding debugging guidelines for NixOS with home-manager
alwaysApply: true
---

GNOME Keybinding Debugging

When custom keybindings don't work in GNOME on NixOS:

1. Check dconf vs nix config sync
```bash
dconf dump /org/gnome/settings-daemon/plugins/media-keys/
```
Compare with home/modules/gnome/dconf.nix. Custom keybinding slot numbers must match.

2. Check if keybinding is being grabbed
```bash
killall gsd-media-keys
env -u GIO_EXTRA_MODULES /usr/libexec/gsd-media-keys 2>&1 &
```
Watch for "Failed to grab accelerator" errors. This means something else holds the keybinding.

3. Common conflicts
- GNOME Shell extensions (wsmatrix, etc.) have default keybindings that override custom ones
- Check extension schemas: `cat ~/.local/share/gnome-shell/extensions/*/schemas/*.xml | grep -i keybind`
- Disable conflicting extension keybindings in dconf.nix

4. Nix/system library conflicts
If gsd-media-keys shows "undefined symbol" or "Failed to load module" errors with Nix paths, the GIO_EXTRA_MODULES environment variable is polluted.
```bash
systemctl --user unset-environment GIO_EXTRA_MODULES
env -u GIO_EXTRA_MODULES /usr/libexec/gsd-media-keys &
```

5. Testing keybindings
```bash
dconf write /path/to/keybinding/command "'touch /tmp/test-file'"
# Press keybinding, then check if file was created
ls /tmp/test-file
```

6. Wayland session restart
Keybinding grabs persist in GNOME Shell on Wayland. After fixing conflicts, user must log out and log back in for changes to take effect.

Key lesson: Always check GNOME Shell extension default keybindings when custom shortcuts fail. Extensions grab keys at a higher priority than gsd-media-keys custom keybindings.
