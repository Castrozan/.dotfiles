#!/usr/bin/env bash
set -euo pipefail

direction="$1"
move_focused_window_with_navigation=false
[[ "${2:-}" == "--move-window" ]] && move_focused_window_with_navigation=true

total_workspace_count="${TOTAL_WORKSPACE_COUNT:?TOTAL_WORKSPACE_COUNT must be set}"
workspace_grid_columns="${WORKSPACE_GRID_COLUMNS:?WORKSPACE_GRID_COLUMNS must be set}"

case "$direction" in
next) workspace_step=1 ;;
prev) workspace_step=-1 ;;
row-down) workspace_step="$workspace_grid_columns" ;;
row-up) workspace_step="-$workspace_grid_columns" ;;
*)
	echo "unknown direction: $direction (expected next|prev|row-down|row-up)" >&2
	exit 1
	;;
esac

focused_workspace="$(aerospace list-workspaces --focused --format '%{workspace}')"
focused_monitor_name="$(aerospace list-workspaces --focused --format '%{monitor-name}')"

target_workspace=$(((focused_workspace - 1 + workspace_step + total_workspace_count) % total_workspace_count + 1))

target_workspace_monitor_name="$(
	aerospace list-workspaces --all --format '%{workspace}|%{monitor-name}' |
		awk -F'|' -v target="$target_workspace" '$1 == target { print $2 }'
)"

if [[ -n "$target_workspace_monitor_name" && "$target_workspace_monitor_name" != "$focused_monitor_name" ]]; then
	aerospace move-workspace-to-monitor --workspace "$target_workspace" "$focused_monitor_name"
fi

if $move_focused_window_with_navigation; then
	aerospace move-node-to-workspace "$target_workspace"
fi

exec aerospace workspace "$target_workspace"
