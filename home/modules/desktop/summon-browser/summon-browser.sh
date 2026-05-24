#!/usr/bin/env bash
set -euo pipefail

application_name="$1"

focused_workspace=$(aerospace list-workspaces --focused)

window_id_and_workspace=$(
	aerospace list-windows --all --format "%{window-id}|%{app-name}|%{workspace}" |
		awk -F'|' -v app="$application_name" '$2 == app { print $1 "|" $3; exit }'
)

if [[ -z "$window_id_and_workspace" ]]; then
	exec /usr/bin/open -a "$application_name"
fi

window_id="${window_id_and_workspace%%|*}"
window_workspace="${window_id_and_workspace##*|}"

if [[ "$window_workspace" == "$focused_workspace" ]]; then
	exec aerospace focus --window-id "$window_id"
fi

exec aerospace move-node-to-workspace \
	--window-id "$window_id" \
	--focus-follows-window \
	"$focused_workspace"
