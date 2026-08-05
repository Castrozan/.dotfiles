#!/usr/bin/env bash
set -Eeuo pipefail

_ensure_wayland_environment() {
	export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
	export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
}

_type_text() {
	local text="$1"
	wtype -- "$text"
}

_parse_and_send_key_combo() {
	local combo="$1"
	local wtype_args=()

	IFS='+' read -ra keys <<<"$combo"
	local last_index=$((${#keys[@]} - 1))

	for i in "${!keys[@]}"; do
		local key="${keys[$i]}"
		key=$(_normalize_key_name "$key")

		if [[ $i -lt $last_index ]]; then
			wtype_args+=("-M" "$key")
		else
			wtype_args+=("-k" "$key")
		fi
	done

	for ((i = last_index - 1; i >= 0; i--)); do
		local key="${keys[$i]}"
		key=$(_normalize_key_name "$key")
		wtype_args+=("-m" "$key")
	done

	wtype "${wtype_args[@]}"
}

_normalize_key_name() {
	local key="$1"
	case "${key,,}" in
	ctrl | control) echo "Control_L" ;;
	alt) echo "Alt_L" ;;
	shift) echo "Shift_L" ;;
	super | logo | mod4 | win) echo "Super_L" ;;
	enter | return) echo "Return" ;;
	esc | escape) echo "Escape" ;;
	backspace) echo "BackSpace" ;;
	delete | del) echo "Delete" ;;
	tab) echo "Tab" ;;
	space) echo "space" ;;
	up) echo "Up" ;;
	down) echo "Down" ;;
	left) echo "Left" ;;
	right) echo "Right" ;;
	home) echo "Home" ;;
	end) echo "End" ;;
	pageup | page_up) echo "Page_Up" ;;
	pagedown | page_down) echo "Page_Down" ;;
	insert | ins) echo "Insert" ;;
	print | prtsc) echo "Print" ;;
	*) echo "$key" ;;
	esac
}

main() {
	local action="${1:-}"
	[[ -z "$action" ]] && {
		echo "Usage: keyboard.sh type \"text\" | key \"combo\"" >&2
		exit 1
	}
	shift

	local value="${1:-}"
	[[ -z "$value" ]] && {
		echo "Usage: keyboard.sh $action \"value\"" >&2
		exit 1
	}

	_ensure_wayland_environment

	case "$action" in
	type) _type_text "$value" ;;
	key) _parse_and_send_key_combo "$value" ;;
	*)
		echo "Unknown action: $action. Use 'type' or 'key'." >&2
		exit 1
		;;
	esac
}

main "$@"
