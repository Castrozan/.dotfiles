# Hyprland Maximize Mode Workflow

## Problem

When using Super+Tab to switch between maximized windows, they resize causing visual jank:
1. Window A is maximized
2. Switch to Window B
3. Window A un-maximizes (resizes down) → **jank**
4. Window B maximizes (resizes up) → **jank**

## Solution: Special Workspace Stacking with Hyprshell Integration

Each window gets its own special workspace where it's alone (always full-size). Hyprshell is configured to show ALL windows and switch to the selected window's workspace.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MAXIMIZE MODE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  special:max_12_addr1        special:max_12_addr2               │
│  ┌─────────────────┐         ┌─────────────────┐                │
│  │                 │         │                 │                │
│  │    Window A     │         │    Window B     │                │
│  │   (full size)   │         │   (full size)   │                │
│  │                 │         │                 │                │
│  └─────────────────┘         └─────────────────┘                │
│                                                                 │
│  Each window is ALONE in its special workspace = always full    │
│  Hyprshell shows all windows, switches to selected workspace    │
│  No resize jank when switching!                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flow

1. **Super+F** (enter maximize mode):
   - Move ALL windows to individual special workspaces
   - Switch to focused window's special workspace
   - Each window is alone = maximized

2. **Super+Tab** (hyprshell):
   - Hyprshell shows ALL windows (no workspace filter)
   - User sees windows from all special workspaces
   - User selects window

3. **Selection made**:
   - Hyprshell switches to selected window's special workspace
   - Window is alone = already maximized
   - **No resize needed = no jank!**

4. **Super+F** (exit maximize mode):
   - Bring all windows back to original workspace
   - Switch to original workspace
   - Normal tiling resumes

### Configuration

**Hyprshell** (`hyprshell.nix`):
```nix
switch = {
  enable = true;
  key = "Tab";
  modifier = "super";
  # No filter_by = shows ALL windows including special workspaces
  switch_workspaces = true;  # Switch to window's workspace when selected
};
```

**Keybinding** (`tiling.conf`):
```conf
bindd = SUPER, F, Maximize mode, exec, omarchy-maximize-mode-toggle
```

### State

- `/tmp/hypr-maximize-mode/<ws_id>` - First line: original workspace, rest: window addresses

### Why This Works

1. **No jank**: Each window is alone in its workspace = always full-size
2. **Hyprshell works**: No filter means all windows visible in picker
3. **Seamless switching**: `switch_workspaces = true` teleports to selected window
4. **Clean exit**: All windows return to original workspace on Super+F

### Trade-offs

- Super+Tab now shows windows from ALL workspaces (not just current)
- When in maximize mode, user is technically on special workspaces
- Workspace indicators in waybar may look different during maximize mode
