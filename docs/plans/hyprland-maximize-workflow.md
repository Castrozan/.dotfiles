# Hyprland Maximize Mode Workflow

## Problem

When using Super+Tab to switch between maximized windows, they resize causing visual jank:
1. Window A is maximized
2. Switch to Window B
3. Window A un-maximizes (resizes down) → **jank**
4. Window B maximizes (resizes up) → **jank**

## Solution: Daemon-Based Swap on Focus Change

Windows stay on the workspace for hyprshell to see. When focus changes, the daemon moves the previous window to a special workspace, leaving the new window alone (maximized).

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MAXIMIZE MODE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Enter maximize mode (Super+F)                               │
│     ┌─────────────────────────────────────────┐                 │
│     │  Workspace 12                           │                 │
│     │  ┌─────────┐  ┌─────────┐  ┌─────────┐  │                 │
│     │  │ Win A   │  │ Win B   │  │ Win C   │  │   Track mode    │
│     │  │(focused)│  │         │  │         │  │   Maximize A    │
│     │  └─────────┘  └─────────┘  └─────────┘  │                 │
│     └─────────────────────────────────────────┘                 │
│                                                                 │
│  2. Super+Tab → hyprshell shows all windows (they're visible)   │
│                                                                 │
│  3. User selects Window B → focus changes                       │
│                                                                 │
│  4. Daemon detects focus change:                                │
│     - Moves A to special:max_12_<addr>                          │
│     - B is now alone = maximized (no resize jank!)              │
│     ┌─────────────────────────────────────────┐                 │
│     │  Workspace 12        special:max_12_... │                 │
│     │  ┌─────────────────┐ ┌─────────┐        │                 │
│     │  │     Win B       │ │  Win A  │        │                 │
│     │  │   (maximized)   │ │(hidden) │        │                 │
│     │  └─────────────────┘ └─────────┘        │                 │
│     └─────────────────────────────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flow

1. **Super+F** (enter maximize mode):
   - Track mode in state file
   - Maximize current window
   - Windows stay on workspace (hyprshell can see them)

2. **Super+Tab** (hyprshell):
   - Shows all windows on current workspace
   - User selects a window

3. **Focus changes** (daemon handles):
   - Move PREVIOUS window to special workspace
   - New window is now alone = maximized
   - No resize jank because previous moved AFTER focus change

4. **Super+F** (exit maximize mode):
   - Bring all windows back from special workspaces
   - Un-maximize current window
   - Normal tiling resumes

### Components

| Component | Purpose |
|-----------|---------|
| `maximize-mode-toggle` | Enter/exit maximize mode |
| `maximize-mode-daemon` | Listen for focus changes, handle swaps |

### State Files

- `/tmp/hypr-maximize-mode/<ws_id>` - Mode active, contains window addresses
- `/tmp/hypr-maximize-mode/<ws_id>_current` - Currently focused window address

### Why This Works

1. **Hyprshell works normally**: Windows stay on workspace during preview
2. **No jank**: Previous window moved to special AFTER focus change
3. **Clean integration**: No changes to hyprshell config needed
4. **Per-workspace**: Each workspace can have independent maximize mode

### Trade-off

There may be a brief visual moment where both windows are visible during the switch, before the daemon moves the previous window. This is minimal and much better than resize jank.
