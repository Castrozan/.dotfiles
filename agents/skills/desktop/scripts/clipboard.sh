#!/usr/bin/env bash
set -Eeuo pipefail

_ensure_wayland_environment() {
	export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
	export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
}

_read_text_clipboard() {
	wl-paste --no-newline 2>/dev/null || echo ""
}

_read_typed_clipboard() {
	local mime_type="$1"
	if [[ "$mime_type" == image/* ]]; then
		local output_path
		output_path="/tmp/clipboard-$(date +%Y%m%d-%H%M%S).${mime_type#image/}"
		wl-paste --type "$mime_type" >"$output_path" 2>/dev/null
		echo "$output_path"
	else
		wl-paste --type "$mime_type" 2>/dev/null || echo ""
	fi
}

_write_text_clipboard() {
	local content="$1"
	echo -n "$content" | wl-copy
}

_write_typed_clipboard() {
	local mime_type="$1"
	wl-copy --type "$mime_type" </dev/stdin
}

main() {
	local action="${1:-}"
	local mime_type=""
	local content=""

	[[ -z "$action" ]] && {
		echo "Usage: clipboard.sh read|write [content] [--type MIME]" >&2
		exit 1
	}
	shift

	local positional_args=()
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--type)
			mime_type="$2"
			shift 2
			;;
		*)
			positional_args+=("$1")
			shift
			;;
		esac
	done

	_ensure_wayland_environment

	case "$action" in
	read)
		if [[ -n "$mime_type" ]]; then
			_read_typed_clipboard "$mime_type"
		else
			_read_text_clipboard
		fi
		;;
	write)
		if [[ -n "$mime_type" ]]; then
			_write_typed_clipboard "$mime_type"
		else
			content="${positional_args[0]:-}"
			[[ -z "$content" ]] && {
				echo "Usage: clipboard.sh write \"content\"" >&2
				exit 1
			}
			_write_text_clipboard "$content"
		fi
		;;
	*)
		echo "Unknown action: $action. Use 'read' or 'write'." >&2
		exit 1
		;;
	esac
}

main "$@"
