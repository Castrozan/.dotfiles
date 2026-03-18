## Window Management

AeroSpace manages virtual workspaces — all windows live on macOS space 1, with AeroSpace hiding inactive workspace windows by moving them offscreen. This means macOS-native tools (AltTab, Mission Control) see every window as being on the same space.

### Cmd+Tab workspace-aware switching

macOS intercepts Cmd+Tab at the WindowServer level before any app can catch it. Karabiner operates at the HID layer, which is lower, so it intercepts Cmd+Tab and runs `hosts/macbook/scripts/workspace-window-switcher` via `shell_command`. The script queries AeroSpace for windows on the focused workspace and presents them through `choose` (a macOS native fuzzy picker). Selecting a window calls `aerospace focus --window-id` to switch to it.

Karabiner's shell environment has no nix PATH, so all binaries in the script use absolute paths (`/usr/bin/python3`, `/etc/profiles/per-user/lucas.zanoni/bin/choose`). The AeroSpace CLI path is resolved dynamically from the running AeroSpace process via `lsof` to survive nix store hash changes.

### Keybinding chain

Karabiner intercepts physical keys first. Removing the Cmd+1-7 → Ctrl+1-7 Karabiner rules was required for AeroSpace keybindings to work — those rules were previously sending Ctrl+N to macOS for native space switching, which meant AeroSpace never received Cmd+N. AeroSpace now handles Cmd+1-7 for workspace switching and Cmd+Tab is routed through Karabiner's shell_command to the switcher script.

### AltTab

Installed via homebrew cask, configured declaratively in `hosts/macbook/default.nix` under `CustomUserPreferences."com.lwouis.alt-tab-macos"`. The `holdShortcut` preference uses a dict format (`{ string = "⌘"; }`) that nix-darwin's `defaults write` does not serialize correctly, so the Cmd+Tab shortcut must be set manually in AltTab's GUI. AltTab is not currently used for Cmd+Tab since the AeroSpace workspace switcher replaced it, but remains installed as a fallback.

### AeroSpace config

`~/.config/aerospace/aerospace.toml` is a mutable file outside the nix store. The backup branch `backup/aerospace-workspaces` in this repo contains the nix module at `home/modules/desktop/aerospace.nix` if declarative management is needed later.
