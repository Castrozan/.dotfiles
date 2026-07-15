## Window Management

The window manager is a custom Hammerspoon virtual-workspace grid (`home/darwin/desktop/hammerspoon/workspace_grid.lua`), **not AeroSpace**. AeroSpace was the prior system; it was dropped because its ad-hoc-signed fork's disk access deadlocked under SophosCryptoGuard, whereas Hammerspoon is notarized (Developer ID) and Sophos trusts it.

The grid simulates a 7x3 = 21-workspace layout on a single macOS Space by show/hiding windows rather than using macOS Spaces: standard windows on the active workspace are maximized (accordion), inactive-workspace windows are parked far offscreen (`x = -1000000`), and dialogs/panels float and restore to their saved position on switch. macOS-native tools (Mission Control, AltTab) therefore see every window as being on the same Space — anything that needs workspace awareness goes through this module.

### Workspace state survives reloads

The window->workspace map and the active workspace are held in memory and **persisted to disk** (`home/darwin/desktop/hammerspoon/workspace_grid_persistence.lua`, default `~/.cache/hammerspoon/workspace-grid-state`) on every change. `init.lua` restores them on load before re-parking windows. Without this, a Hammerspoon reload — which **every config redeploy on rebuild triggers** — would wipe the in-memory map and collapse every window onto workspace 1. The state file format is plain text: first line is the active workspace number, each remaining line is `<window-id> <workspace-number>`.

### Cmd+Tab — workspace-aware switching

macOS intercepts Cmd+Tab at the WindowServer level before any app can catch it. Karabiner operates at the HID layer (lower) and wins the race; the rule sends a UNIX datagram into the workspace-window-switcher daemon at `/tmp/workspace-switcher.sock`. The daemon (`hosts/shared-darwin/workspace-window-switcher/`, Swift) renders an MRU-ordered overlay and handles the hold-cmd / cycle / release-to-commit interaction. It reads the active workspace's windows from a JSON file that `switcher_bridge.lua` keeps fresh (`/tmp/workspace-window-switcher-windows.json`) and requests focus by writing a window id to a file that module watches (`/tmp/workspace-window-switcher-focus-request`) — keeping focus in Hammerspoon avoids the daemon needing its own Accessibility/Screen-Recording grants. The IPC mechanism is documented in `home/darwin/desktop/karabiner/README.md`.

### Keybindings

Bound in `init.lua`: Cmd+1..7 switch workspace, Cmd+Shift+1..7 move the focused window to a workspace, Ctrl+Alt+arrows (and Cmd+Alt+arrows) navigate the grid, Ctrl+Alt+Shift+arrows (and Cmd+Alt+Shift+arrows) carry the focused window with you. Summon the personal Chrome profile (Cmd+B) and Chrome Global (Cmd+C) to the current workspace is invoked from Karabiner (via `hs -c`) rather than an `hs.hotkey`, so the Karabiner Ctrl+C→Cmd+C remap does not steal copy.

### AltTab

Installed via homebrew cask as a fallback. Unused for Cmd+Tab now that the workspace-window-switcher daemon exists.
