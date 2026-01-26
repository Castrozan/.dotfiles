# Hyprland Maximize Mode Workflow

## Problem

When using Super+Tab to switch between maximized windows, they resize causing visual jank:
1. Window A is maximized
2. Switch to Window B
3. Window A un-maximizes (resizes down) → **jank**
4. Window B maximizes (resizes up) → **jank**

## Status: Incomplete

This feature is partially implemented but has unresolved issues. The core concept works but the integration with keybindings and hyprshell is problematic.

## Attempted Approach: Multiple Special Workspaces

Each window gets its own special workspace so it's always alone (= always full size). Switching toggles between special workspaces instead of moving windows, avoiding resize jank.

### What Works

- Moving windows to individual special workspaces
- Toggling between special workspaces (no resize jank)
- Bringing windows back to regular workspace

### What Doesn't Work

1. **Hyprshell intercepts Super+Tab globally**: Hyprshell registers a global keybinding that bypasses Hyprland submaps. Even with hyprshell stopped, the binding needs to be manually added at runtime.

2. **Focus loss causes hidden windows**: When using special workspaces, if focus is lost (e.g., clicking elsewhere), all windows become hidden with no easy way to recover.

3. **Super+Tab binding not loading from config**: For unknown reasons, `bindd = SUPER, TAB, ...` in the maximize submap config file doesn't load, while other bindings in the same file work fine.

## Components Created

| File | Purpose |
|------|---------|
| `bin/omarchy/maximize-mode-toggle` | Enter/exit maximize mode |
| `bin/omarchy/maximize-mode-switcher` | Switch between windows in maximize mode |
| `.config/hypr/omarchy/bindings/maximize-submap.conf` | Keybindings for maximize mode |

## Alternative Approaches to Explore

1. **Hyprland Groups**: Use the built-in group/tab feature which may handle this use case better.

2. **Custom hyprshell filter**: Modify hyprshell to support filtering by window tags or maximize mode state.

3. **Different keybinding**: Use Super+` or another key instead of Super+Tab to avoid hyprshell conflict.

4. **Patch hyprshell**: Add maximize-mode awareness to hyprshell so it handles special workspaces correctly.

## Manual Testing Commands

```bash
# Enter maximize mode manually
hyprctl dispatch movetoworkspacesilent "special:max_12_test,address:0x..."
hyprctl dispatch togglespecialworkspace "max_12_test"

# Switch by toggling workspaces
hyprctl dispatch togglespecialworkspace "max_12_win_a"
hyprctl dispatch togglespecialworkspace "max_12_win_b"

# Bring window back
hyprctl dispatch movetoworkspace "12,address:0x..."
```

## Lessons Learned

1. Special workspaces are fragile - easy to lose focus and have hidden windows
2. Hyprshell's global keybinding registration bypasses Hyprland's submap system
3. Some keybindings don't load from config files for unclear reasons
4. The approach of keeping each window in its own special workspace does eliminate resize jank, but the UX issues make it impractical
