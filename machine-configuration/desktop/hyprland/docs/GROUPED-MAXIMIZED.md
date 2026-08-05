# Scrolling Layout Architecture

Every workspace uses Hyprland's scrolling layout (`general:layout = scrolling`) with `column_width = 1.0` and `fullscreen_on_one_column = true`. Each window occupies a full-width column on an infinite horizontal tape. Only one column is visible at a time; navigating between windows means scrolling left or right with `layoutmsg focus l/r`. This turns the tiling compositor into a tabbed window manager without needing Hyprland groups.

## MRU Focus on Close

`input:focus_on_close = 2` tells Hyprland to focus the most recently used window when a window closes, rather than the spatially adjacent column. This is native compositor behavior — no daemon intervention needed.

## Focus Daemon

The focus daemon (`scripts/windows/focus_daemon.py`) listens on Hyprland's IPC socket for `activewindowv2` events and manages floating window visibility. When a tiled window gains focus, unpinned floating windows are moved offscreen. When a floating window gains focus, it is restored to center.

## Window Movement

Moving a window between workspaces uses `hypr-move-window-to-workspace`, which dispatches `focuswindow` (if a specific address is given) followed by `movetoworkspace`. In silent mode it returns to the previous workspace afterward. The scrolling layout handles column placement automatically at the destination.

## Show Desktop

The show-desktop toggle (`scripts/windows/show_desktop.py`) saves all window addresses on the active workspace to a state file, moves them to `special:desktop`, and restores them on second invocation with focus preservation.

## Close Window History

When a window is closed via `close_window_cycle.py`, the script saves the window command to a reopen history file before dispatching `killactive`. Focus recovery is handled natively by `input:focus_on_close = 2`.
