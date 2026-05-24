## Window Management

AeroSpace is the window manager. All windows live on macOS Space 1; AeroSpace simulates virtual workspaces by moving inactive ones offscreen rather than using macOS Spaces. macOS-native tools (Mission Control, AltTab) therefore see every window as being on the same space — anything that needs workspace awareness has to go through AeroSpace's CLI or socket.

AeroSpace's config lives at `~/.config/aerospace/aerospace.toml` as a mutable file outside the nix store. The backup branch `backup/aerospace-workspaces` carries the corresponding nix module at `home/modules/desktop/aerospace.nix` if declarative management is wanted later.

### Cmd+Tab — workspace-aware switching

macOS intercepts Cmd+Tab at the WindowServer level before any app can catch it. Karabiner operates at the HID layer (lower) and wins the race; the rule fires `to.send_user_command` which sends a UNIX datagram directly into the workspace-window-switcher daemon at `/tmp/workspace-switcher.sock`. The daemon queries AeroSpace for windows on the focused workspace, presents an MRU-ordered overlay, and on commit calls `aerospace focus --window-id` to switch. End-to-end keystroke handling is sub-millisecond on the karabiner side. The IPC mechanism and why it replaced the previous fork+exec path is documented in `home/modules/desktop/karabiner/README.md`. Daemon sources live at `hosts/macbook/scripts/workspace-window-switcher-daemon-swift-sources/`.

### AltTab

Installed via homebrew cask, configured declaratively in `hosts/macbook/default.nix` under `CustomUserPreferences."com.lwouis.alt-tab-macos"`. The `holdShortcut` preference uses a dict format that nix-darwin's `defaults write` does not serialize correctly, so the Cmd+Tab shortcut must be set manually in AltTab's GUI. AltTab is unused for Cmd+Tab now that the AeroSpace workspace switcher exists, but remains installed as a fallback.
