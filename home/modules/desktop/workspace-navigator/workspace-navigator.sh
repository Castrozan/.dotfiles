#!/usr/bin/env bash
set -euo pipefail

direction="$1"
move_focused_window_with_navigation=false
[[ "${2:-}" == "--move-window" ]] && move_focused_window_with_navigation=true

workspace_state=$(
	aerospace list-workspaces --all \
		--format '%{workspace}|%{monitor-name}|%{workspace-is-focused}|%{workspace-is-visible}'
)

target_workspace_and_monitor_pair=$(
	printf '%s\n' "$workspace_state" |
		awk -F'|' -v direction="$direction" '
			{
				ordered_workspaces[NR] = $1
				monitor_name_for_workspace[$1] = $2
				if ($3 == "true") {
					focused_workspace = $1
					focused_monitor_name = $2
				}
				if ($4 == "true" && $3 != "true") {
					workspace_is_visible_on_other_monitor[$1] = 1
				}
				total_workspace_count = NR
			}
			END {
				navigable_count = 0
				focused_position_in_navigable = -1
				for (position = 1; position <= total_workspace_count; position++) {
					candidate = ordered_workspaces[position]
					if (!(candidate in workspace_is_visible_on_other_monitor)) {
						navigable_workspaces[navigable_count] = candidate
						if (candidate == focused_workspace) {
							focused_position_in_navigable = navigable_count
						}
						navigable_count++
					}
				}
				if (direction == "next") {
					target_position = (focused_position_in_navigable + 1) % navigable_count
				} else {
					target_position = (focused_position_in_navigable - 1 + navigable_count) % navigable_count
				}
				target_workspace = navigable_workspaces[target_position]
				printf "%s|%s|%s\n", target_workspace, monitor_name_for_workspace[target_workspace], focused_monitor_name
			}
		'
)

IFS='|' read -r target_workspace target_workspace_monitor_name focused_monitor_name <<<"$target_workspace_and_monitor_pair"

if [[ "$target_workspace_monitor_name" != "$focused_monitor_name" ]]; then
	aerospace move-workspace-to-monitor --workspace "$target_workspace" "$focused_monitor_name"
fi

if $move_focused_window_with_navigation; then
	aerospace move-node-to-workspace "$target_workspace"
fi

exec aerospace workspace "$target_workspace"
