# Grouped-Maximized Architecture

Every workspace operates as a tab group. All tiled windows on a workspace are merged into a single Hyprland group and maximized (`fullscreen 1`), turning the tiling compositor into a tabbed window manager. Switching between windows means switching group tabs, not spatially navigating tiles.

## How It Works

Three mechanisms enforce the pattern at different layers.

**Window rules** in `conf.d/windows.conf` make every new window tile and invade the existing group on arrival (`tile on` + `group invade` on all classes). The config option `group:group_on_movetoworkspace` ensures windows moved between workspaces auto-join the destination group. Together, these two rules mean any window appearing on any workspace — whether launched, moved, or summoned — joins the group without script intervention.

**The maximize-focus daemon** (`scripts/windows/maximize_focus_daemon.py`) listens on Hyprland's IPC socket and tracks which workspaces have maximized windows. When a maximized window is closed, the daemon force-remaximizes (`fullscreen 1 unset` then `fullscreen 1 set`) to correct stale geometry, then regroups remaining windows. It also manages floating window visibility — unpinned floating windows are moved offscreen when a tiled window gains focus and restored to center when re-focused.

**The toggle script** (`scripts/windows/toggle_group_for_all_workspace_windows.py`) is the escape hatch. It either groups all tiled windows on the active workspace into one group and maximizes, or dissolves the group back into tiled layout. Bound to `SUPER+T`, it lets the user temporarily tile for spatial arrangement, then re-tab.

## Shared Grouping Library

Core grouping logic lives in `scripts/windows/lib/workspace_grouping.py`. Both the toggle script and the guard scripts import from this shared module instead of shelling out to each other. This eliminates race conditions where two concurrent callers (daemon + close script) could trigger a toggle that dissolves the group instead of preserving it.

## The Detach-Move-Merge Pattern

Moving a window between workspaces requires more than `movetoworkspace` because the window may be inside a group. Every script that relocates windows follows the same sequence: `moveoutofgroup` to detach from the source group, `movetoworkspace` to send it to the target, then `moveintogroup` in all four directions as a shotgun approach to merge into whatever group exists at the destination, followed by `fullscreen 1` to re-maximize. This pattern appears in `scripts/windows/detach_from_group_and_move_to_workspace.py` (bound to `SUPER+SHIFT+[0-9]` and grid navigation), `scripts/launchers/summon_brave.py`, and `scripts/launchers/summon_chrome_global.py`.

## Guard Scripts

Some operations break the grouped state temporarily. The launcher (`scripts/launchers/super_launcher.py`) must ungroup the workspace so fuzzel can tile alongside existing windows, then regroup after the launched app settles. The show-desktop toggle (`scripts/windows/show_desktop.py`) dissolves groups before hiding windows to special workspace, then regroups on restore. Both use `ensure_workspace_grouped.py` and `ensure_workspace_tiled.py` as guards that check state before acting — the ensure scripts use the shared grouping library directly to avoid toggle races.

## Close Window Recovery

When a window is closed (via `close_window_cycle.py` keybind or external kill like `pkill`), two recovery paths fire:

1. **The close script** saves the window to reopen history, focuses the previous window on the workspace, force-remaximizes, and regroups.
2. **The daemon** catches the `closewindow` IPC event, restores focus from its history, force-remaximizes, and regroups.

Both paths call `ensure_workspace_grouped` which is idempotent — calling it twice is harmless since it only groups if not already grouped, and never dissolves.

The force-remaximize (`fullscreen 1 unset` + `fullscreen 1 set`) exists because Hyprland can report `fullscreen: 1` while the actual window geometry is corrupted to half-screen after a group member is killed externally.

## Constraints

The `group invade` window rule handles most cases, but grouped state can break when: multiple windows spawn simultaneously (race between group joins), windows are dragged with the mouse outside the group, or special workspaces interact with regular ones. The daemon and guard scripts exist to recover from these edge cases. The groupbar is disabled (`group:groupbar:enabled = false`) since the quickshell bar handles tab display through its own IPC queries.

Hyprland v0.54.0+ includes native focus history walking within groups (PR #12763) and geometry preservation for maximized windows (PR #13535). These upstream fixes reduce but do not eliminate the need for the daemon's recovery logic, since external kills and race conditions still produce states that require active correction.
