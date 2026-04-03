# Scrolling Layout Architecture

Every workspace uses Hyprland's scrolling layout (`general:layout = scrolling`) with `column_width = 1.0` and `fullscreen_on_one_column = true`. Each window occupies a full-width column on an infinite horizontal tape. Only one column is visible at a time; navigating between windows means scrolling left or right with `layoutmsg focus l/r`. This turns the tiling compositor into a tabbed window manager without needing Hyprland groups.

## Focus Daemon

The focus daemon (`scripts/windows/focus_daemon.py`) listens on Hyprland's IPC socket for two events. On `activewindowv2`, it maintains a two-entry focus history and manages floating window visibility — unpinned floating windows are moved offscreen when a tiled window gains focus and restored to center when re-focused. On `closewindow`, it restores focus to the previously focused window.

## Window Movement

Moving a window between workspaces uses `hypr-move-window-to-workspace`, which dispatches `focuswindow` (if a specific address is given) followed by `movetoworkspace`. In silent mode it returns to the previous workspace afterward. The scrolling layout handles column placement automatically at the destination.

## Show Desktop

The show-desktop toggle (`scripts/windows/show_desktop.py`) saves all window addresses on the active workspace to a state file, moves them to `special:desktop`, and restores them on second invocation with focus preservation.

## Close Window Recovery

When a window is closed via `close_window_cycle.py`, the script saves the window command to a reopen history file, kills the active window, then focuses the previous window on the workspace by `focusHistoryID` sort order. The daemon also catches the close event and restores focus from its own two-entry history.
