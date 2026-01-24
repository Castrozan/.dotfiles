# Hyprland Maximize Workflow

## Problem

When using Super+Tab (hyprshell window switcher), windows lose their maximized state and revert to tiled layout. This causes apps to resize themselves, creating a janky user experience.

**Current behavior:**
1. Window A is maximized (Super+F, `fullscreen 1`)
2. Super+Tab to Window B
3. Window A loses maximize state, returns to tiled
4. When switching back, Window A needs to resize again

## Proposed Solutions

### Option 1: Window Rule (Simple but incomplete)
```conf
windowrulev2 = maximize, class:.*
```
- All new windows start maximized
- Does NOT preserve maximize on focus change
- Same resize problem persists

### Option 2: One-window-per-workspace (GNOME-like)
Put each app in its own workspace. Navigate workspaces instead of windows.
- Clean, each app always has full screen
- No resize jank since window is always alone in workspace
- Changes mental model, more workspaces to manage
- Super+Tab becomes workspace switch

### Option 3: IPC Daemon Auto-Maximize (Recommended)
A systemd user service listening to Hyprland's `activewindow` event that immediately maximizes the focused window:

```bash
#!/usr/bin/env bash
socat -U - UNIX-CONNECT:$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock | while read -r line; do
  if [[ "$line" =~ ^activewindow ]]; then
    hyprctl dispatch fullscreen 1
  fi
done
```

- Keeps current workflow with hyprshell visual preview
- Windows always maximized on focus
- Slight visual flash during maximize transition
- Requires systemd service management

### Option 4: Custom Super+Tab Script
Replace hyprshell's switcher with a script that switches AND maximizes atomically.
- Precise control over behavior
- Loses hyprshell's visual preview feature

### Option 5: Special Workspace Stacking
Move unfocused windows to a special workspace, pull focused one to current workspace.
- True single-window view (only one tiled = full size)
- Complex implementation
- May break window focus history

## Recommendation

**Option 3 (IPC Daemon)** provides the smoothest experience:
- Preserves hyprshell visual preview on Super+Tab
- Every window auto-maximizes on focus
- Minimal config changes
- Can be toggled via systemd

## Implementation Plan

1. Create `omarchy-maximize-daemon` script in `home/modules/hyprland/omarchy-scripts.nix`
2. Add systemd user service to start daemon with Hyprland session
3. Update user bindings if needed
4. Test with various apps (terminals, browsers, editors)
