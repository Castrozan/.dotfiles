#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCREENSHOT_DEFAULT_DIR="/tmp"

_ensure_wayland_environment() {
	export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
	export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
}

_generate_output_path() {
	local timestamp
	timestamp=$(date +%Y%m%d-%H%M%S)
	echo "${SCREENSHOT_DEFAULT_DIR}/screenshot-${timestamp}.png"
}

_get_active_window_geometry() {
	hyprctl activewindow -j | jq -r '"\(.at[0]),\(.at[1]) \(.size[0])x\(.size[1])"'
}

_capture_full_desktop() {
	local output_path="$1"
	grim "$output_path"
}

_capture_region_interactive() {
	local output_path="$1"
	local selected_region
	selected_region=$(slurp)
	grim -g "$selected_region" "$output_path"
}

_capture_active_window() {
	local output_path="$1"
	local window_geometry
	window_geometry=$(_get_active_window_geometry)
	grim -g "$window_geometry" "$output_path"
}

main() {
	local capture_mode="full"
	local output_path=""

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--region)
			capture_mode="region"
			shift
			;;
		--active)
			capture_mode="active"
			shift
			;;
		--output)
			output_path="$2"
			shift 2
			;;
		*)
			echo "Unknown option: $1" >&2
			exit 1
			;;
		esac
	done

	_ensure_wayland_environment
	[[ -z "$output_path" ]] && output_path=$(_generate_output_path)

	case "$capture_mode" in
	full) _capture_full_desktop "$output_path" ;;
	region) _capture_region_interactive "$output_path" ;;
	active) _capture_active_window "$output_path" ;;
	esac

	echo "$output_path"
}

main "$@"
