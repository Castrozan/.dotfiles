#!/usr/bin/env bash

set -Eeuo pipefail

readonly WORKSPACE_SLOTS=7
readonly WAYBAR_WORKSPACE_FILE_PREFIX="/tmp/waybar-ws"
readonly HYPRLAND_SOCKET_PATH="${XDG_RUNTIME_DIR}/hypr/${HYPRLAND_INSTANCE_SIGNATURE}/.socket2.sock"

main() {
	_initialize_workspace_slot_files
	_listen_for_workspace_events_and_update
}

_initialize_workspace_slot_files() {
	local batch_json
	batch_json=$(hyprctl -j --batch 'activeworkspace; workspaces') || return

	local all_slots_json
	all_slots_json=$(_compute_all_slots_json "$batch_json") || return
	[[ -z "$all_slots_json" ]] && return

	local line
	while IFS= read -r line; do
		local slot="${line%%:*}"
		local json="${line#*:}"
		local target_file="${WAYBAR_WORKSPACE_FILE_PREFIX}${slot}"
		printf '%s\n' "$json" >"$target_file"
	done <<<"$all_slots_json"
}

_update_workspace_slot_files() {
	local batch_json
	batch_json=$(hyprctl -j --batch 'activeworkspace; workspaces') || return

	local all_slots_json
	all_slots_json=$(_compute_all_slots_json "$batch_json") || return
	[[ -z "$all_slots_json" ]] && return

	local line
	while IFS= read -r line; do
		local slot="${line%%:*}"
		local json="${line#*:}"
		local target_file="${WAYBAR_WORKSPACE_FILE_PREFIX}${slot}"
		printf '%s\n' "$json" >>"$target_file"
	done <<<"$all_slots_json"
}

_compute_all_slots_json() {
	local batch_output="$1"
	printf '%s' "$batch_output" | jq -s -r --argjson slots "$WORKSPACE_SLOTS" '
    (.[0].id // empty) as $active |
    if $active == null then empty else
      ((($active - 1) / $slots | floor) * $slots + 1) as $page_start |
      [.[1][] | {(.id | tostring): .windows}] | add // {} |
      . as $window_map |
      range(1; $slots + 1) |
      . as $slot |
      ($page_start + $slot - 1) as $target |
      ($window_map[$target | tostring] // 0) as $windows |
      (if $active == $target then "active"
       elif $windows > 0 then "occupied"
       else "empty" end) as $class |
      "\($slot):{\"text\":\"\($target)\",\"class\":\"\($class)\"}"
    end
  '
}

_listen_for_workspace_events_and_update() {
	nc -U "$HYPRLAND_SOCKET_PATH" 2>/dev/null | while IFS= read -r event; do
		case "$event" in
		workspace* | movewindow* | createworkspace* | destroyworkspace* | focusedmon*)
			_update_workspace_slot_files
			;;
		esac
	done
}

main "$@"
