#!/usr/bin/env bash

set -Eeuo pipefail

readonly WORKSPACE_SLOTS=7

main() {
	local slot="${1:-}"

	if [[ -z "$slot" || ! "$slot" =~ ^[1-7]$ ]]; then
		exit 1
	fi

	_switch_to_workspace_slot "$slot"
}

_switch_to_workspace_slot() {
	local slot="$1"

	local active_workspace_id
	active_workspace_id=$(hyprctl activeworkspace -j | jq -r '.id // empty')
	[[ -z "$active_workspace_id" ]] && exit 1

	local page_start=$((((active_workspace_id - 1) / WORKSPACE_SLOTS) * WORKSPACE_SLOTS + 1))
	local target_workspace=$((page_start + slot - 1))

	hyprctl dispatch workspace "$target_workspace" >/dev/null
}

main "$@"
