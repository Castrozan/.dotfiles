#!/usr/bin/env bash
set -Eeuo pipefail

readonly OUTPUT_DIR="/tmp"

_ensure_wayland_environment() {
	export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
	export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
}

_generate_output_path() {
	local timestamp
	timestamp=$(date +%Y%m%d-%H%M%S)
	echo "${OUTPUT_DIR}/screenshot-${timestamp}.png"
}

_get_active_window_geometry() {
	local x y w h
	read -r x y w h < <(hyprctl activewindow -j | jq -r '.at[0], .at[1], .size[0], .size[1]' | tr '\n' ' ')
	echo "${x},${y} ${w}x${h}"
}

_capture_full() {
	local output_path="$1"
	grim "$output_path"
}

_capture_region() {
	local output_path="$1"
	local region
	region=$(slurp)
	grim -g "$region" "$output_path"
}

_capture_window() {
	local output_path="$1"
	local geometry
	geometry=$(_get_active_window_geometry)
	grim -g "$geometry" "$output_path"
}

main() {
	local mode="full"

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--full)
			mode="full"
			shift
			;;
		--region)
			mode="region"
			shift
			;;
		--window)
			mode="window"
			shift
			;;
		*)
			echo "Unknown option: $1" >&2
			exit 1
			;;
		esac
	done

	_ensure_wayland_environment
	local output_path
	output_path=$(_generate_output_path)

	case "$mode" in
	full) _capture_full "$output_path" ;;
	region) _capture_region "$output_path" ;;
	window) _capture_window "$output_path" ;;
	esac

	echo "$output_path"
}

main "$@"
