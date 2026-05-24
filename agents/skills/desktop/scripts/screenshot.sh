#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCREENSHOT_DEFAULT_DIR="/tmp"

_generate_output_path() {
	local timestamp
	timestamp=$(date +%Y%m%d-%H%M%S)
	echo "${SCREENSHOT_DEFAULT_DIR}/screenshot-${timestamp}.png"
}

_capture_darwin_full() {
	screencapture -x "$1"
}

_capture_darwin_region() {
	screencapture -x -i "$1"
}

_capture_darwin_active() {
	screencapture -x -l "$(osascript -e 'tell application "System Events" to return id of first window of (first process whose frontmost is true)')" "$1"
}

_ensure_wayland_environment() {
	export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
	export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
}

_get_active_window_geometry() {
	hyprctl activewindow -j | jq -r '"\(.at[0]),\(.at[1]) \(.size[0])x\(.size[1])"'
}

_capture_linux_full() {
	_ensure_wayland_environment
	grim "$1"
}

_capture_linux_region() {
	_ensure_wayland_environment
	local selected_region
	selected_region=$(slurp)
	grim -g "$selected_region" "$1"
}

_capture_linux_active() {
	_ensure_wayland_environment
	local window_geometry
	window_geometry=$(_get_active_window_geometry)
	grim -g "$window_geometry" "$1"
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

	[[ -z "$output_path" ]] && output_path=$(_generate_output_path)

	local platform
	platform="$(uname -s)"

	case "${platform}-${capture_mode}" in
	Darwin-full) _capture_darwin_full "$output_path" ;;
	Darwin-region) _capture_darwin_region "$output_path" ;;
	Darwin-active) _capture_darwin_active "$output_path" ;;
	*-full) _capture_linux_full "$output_path" ;;
	*-region) _capture_linux_region "$output_path" ;;
	*-active) _capture_linux_active "$output_path" ;;
	esac

	echo "$output_path"
}

main "$@"
