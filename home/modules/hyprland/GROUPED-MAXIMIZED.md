# Grouped-Maximized Architecture

Every workspace operates as a tab group. All tiled windows on a workspace are merged into a single Hyprland group and maximized (`fullscreen 1`), turning the tiling compositor into a tabbed window manager. Switching between windows means switching group tabs, not spatially navigating tiles.

## How It Works

Three mechanisms enforce the pattern at different layers.

**Window rules** in `conf.d/windows.conf` make every new window tile and invade the existing group on arrival (`tile on` + `group invade` on all classes). The config option `group:group_on_movetoworkspace` ensures windows moved between workspaces auto-join the destination group. Together, these two rules mean any window appearing on any workspace — whether launched, moved, or summoned — joins the group without script intervention.

**The maximize-focus daemon** (`bin/hypr/maximize-focus-daemon`) listens on Hyprland's IPC socket and tracks which workspaces have maximized windows. When a maximized window is closed, the daemon re-maximizes the next window in the group. It also maintains a two-deep focus history so the previously-focused window receives focus on close, preserving the user's mental stack.

**The toggle script** (`bin/hypr/toggle-group-for-all-workspace-windows`) is the escape hatch. It either groups all tiled windows on the active workspace into one group and maximizes, or dissolves the group back into tiled layout. Bound to `SUPER+T`, it lets the user temporarily tile for spatial arrangement, then re-tab.

## The Detach-Move-Merge Pattern

Moving a window between workspaces requires more than `movetoworkspace` because the window may be inside a group. Every script that relocates windows follows the same sequence: `moveoutofgroup` to detach from the source group, `movetoworkspace` to send it to the target, then `moveintogroup` in all four directions as a shotgun approach to merge into whatever group exists at the destination, followed by `fullscreen 1` to re-maximize. This pattern appears in `bin/hypr/detach-from-group-and-move-to-workspace` (bound to `SUPER+SHIFT+[0-9]` and grid navigation), `bin/hypr/summon-brave`, and `bin/hypr/summon-chrome-global`.

## Guard Scripts

Some operations break the grouped state temporarily. The launcher (`bin/hypr/super-launcher`) must ungroup the workspace so fuzzel can tile alongside existing windows, then regroup after the launched app settles. The show-desktop toggle (`bin/hypr/show-desktop`) dissolves groups before hiding windows to special workspace, then regroups on restore. Both use `bin/hypr/ensure-workspace-grouped` and `bin/hypr/ensure-workspace-tiled` as guards that check whether all tiled windows on the workspace are already in a single group before acting.

## Constraints

The `group invade` window rule handles most cases, but grouped state can break when: multiple windows spawn simultaneously (race between group joins), windows are dragged with the mouse outside the group, or special workspaces interact with regular ones. The daemon and guard scripts exist to recover from these edge cases. The groupbar is disabled (`group:groupbar:enabled = false`) since the quickshell bar handles tab display through its own IPC queries.
