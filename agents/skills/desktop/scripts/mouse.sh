#!/usr/bin/env bash
set -Eeuo pipefail

readonly YDOTOOL_SOCKET="/tmp/.ydotool_socket"

_ensure_ydotoold_running() {
	if [[ ! -S "$YDOTOOL_SOCKET" ]]; then
		ydotoold &
		local retries=0
		while [[ ! -S "$YDOTOOL_SOCKET" && $retries -lt 20 ]]; do
			sleep 0.1
			retries=$((retries + 1))
		done
		[[ -S "$YDOTOOL_SOCKET" ]] || {
			echo "Failed to start ydotoold" >&2
			exit 1
		}
	fi
}

_resolve_button_code() {
	local button_name="${1:-left}"
	case "$button_name" in
	left) echo "0x110" ;;
	right) echo "0x111" ;;
	middle) echo "0x112" ;;
	*)
		echo "Unknown button: $button_name" >&2
		exit 1
		;;
	esac
}

_move_cursor_to_absolute_position() {
	local target_x="$1"
	local target_y="$2"
	ydotool mousemove --absolute -x "$target_x" -y "$target_y"
}

_perform_click_at_position() {
	local target_x="$1"
	local target_y="$2"
	local button_name="${3:-left}"
	local double_click="${4:-false}"

	local button_code
	button_code=$(_resolve_button_code "$button_name")

	_move_cursor_to_absolute_position "$target_x" "$target_y"
	sleep 0.05

	ydotool click "$button_code"
	if [[ "$double_click" == "true" ]]; then
		sleep 0.05
		ydotool click "$button_code"
	fi
}

_perform_scroll() {
	local direction="$1"
	local amount="${2:-3}"

	case "$direction" in
	up) ydotool mousemove -- -x 0 -y 0 && ydotool click --next-delay 15 "0x40004" --repeat "$amount" ;;
	down) ydotool mousemove -- -x 0 -y 0 && ydotool click --next-delay 15 "0x40005" --repeat "$amount" ;;
	left) ydotool mousemove -- -x 0 -y 0 && ydotool click --next-delay 15 "0x40006" --repeat "$amount" ;;
	right) ydotool mousemove -- -x 0 -y 0 && ydotool click --next-delay 15 "0x40007" --repeat "$amount" ;;
	*)
		echo "Unknown scroll direction: $direction. Use up/down/left/right." >&2
		exit 1
		;;
	esac
}

_perform_drag_between_positions() {
	local start_x="$1"
	local start_y="$2"
	local end_x="$3"
	local end_y="$4"

	_move_cursor_to_absolute_position "$start_x" "$start_y"
	sleep 0.05
	ydotool mousedown 0x110
	sleep 0.1
	_move_cursor_to_absolute_position "$end_x" "$end_y"
	sleep 0.05
	ydotool mouseup 0x110
}

main() {
	local action="${1:-}"
	[[ -z "$action" ]] && {
		echo "Usage: mouse.sh click|move|scroll|drag [args]" >&2
		exit 1
	}
	shift

	_ensure_ydotoold_running

	case "$action" in
	click)
		local target_x="${1:-}" target_y="${2:-}" button_name="left" double_click="false"
		[[ -z "$target_x" || -z "$target_y" ]] && {
			echo "Usage: mouse.sh click X Y [--button left|right|middle] [--double]" >&2
			exit 1
		}
		shift 2
		while [[ $# -gt 0 ]]; do
			case "$1" in
			--button)
				button_name="$2"
				shift 2
				;;
			--double)
				double_click="true"
				shift
				;;
			*) shift ;;
			esac
		done
		_perform_click_at_position "$target_x" "$target_y" "$button_name" "$double_click"
		;;
	move)
		local target_x="${1:-}" target_y="${2:-}"
		[[ -z "$target_x" || -z "$target_y" ]] && {
			echo "Usage: mouse.sh move X Y" >&2
			exit 1
		}
		_move_cursor_to_absolute_position "$target_x" "$target_y"
		;;
	scroll)
		local direction="${1:-}" amount="${2:-3}"
		[[ -z "$direction" ]] && {
			echo "Usage: mouse.sh scroll up|down|left|right [amount]" >&2
			exit 1
		}
		_perform_scroll "$direction" "$amount"
		;;
	drag)
		local start_x="${1:-}" start_y="${2:-}" end_x="${3:-}" end_y="${4:-}"
		[[ -z "$start_x" || -z "$start_y" || -z "$end_x" || -z "$end_y" ]] && {
			echo "Usage: mouse.sh drag X1 Y1 X2 Y2" >&2
			exit 1
		}
		_perform_drag_between_positions "$start_x" "$start_y" "$end_x" "$end_y"
		;;
	*)
		echo "Unknown action: $action. Use click, move, scroll, or drag." >&2
		exit 1
		;;
	esac
}

main "$@"
