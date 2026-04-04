#!/usr/bin/env bash
set -Eeuo pipefail

readonly IMAGE_TMP_DIR="/tmp"
readonly IMAGE_TMP_PREFIX="clipboard"

_ensure_wayland_env() {
	export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
	export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
}

_read() {
	local mime_type="$1"
	if [[ -z "$mime_type" ]]; then
		wl-paste --no-newline 2>/dev/null || echo ""
	elif [[ "$mime_type" == image/* ]]; then
		local ext="${mime_type#image/}"
		local output="${IMAGE_TMP_DIR}/${IMAGE_TMP_PREFIX}-$(date +%Y%m%d-%H%M%S).${ext}"
		wl-paste --type "$mime_type" >"$output" 2>/dev/null
		echo "$output"
	else
		wl-paste --type "$mime_type" 2>/dev/null || echo ""
	fi
}

_write() {
	local content="$1"
	echo -n "$content" | wl-copy
}

_write_stdin() {
	wl-copy
}

_watch() {
	wl-paste --watch cat
}

main() {
	local subcommand="${1:-}"
	if [[ -z "$subcommand" ]]; then
		echo "Usage: clipboard.sh read|write|watch [--type MIME] [text]" >&2
		exit 1
	fi
	shift

	_ensure_wayland_env

	case "$subcommand" in
	read)
		local mime_type=""
		while [[ $# -gt 0 ]]; do
			case "$1" in
			--type)
				mime_type="$2"
				shift 2
				;;
			*) shift ;;
			esac
		done
		_read "$mime_type"
		;;
	write)
		local mime_type=""
		local positional=()
		while [[ $# -gt 0 ]]; do
			case "$1" in
			--type)
				mime_type="$2"
				shift 2
				;;
			*)
				positional+=("$1")
				shift
				;;
			esac
		done
		if [[ -n "$mime_type" ]]; then
			wl-copy --type "$mime_type"
		elif [[ ${#positional[@]} -gt 0 ]]; then
			_write "${positional[0]}"
		elif ! [[ -t 0 ]]; then
			_write_stdin
		else
			echo "Usage: clipboard.sh write \"text\"  OR  echo text | clipboard.sh write" >&2
			exit 1
		fi
		;;
	watch)
		_watch
		;;
	*)
		echo "Unknown subcommand: $subcommand. Use read, write, or watch." >&2
		exit 1
		;;
	esac
}

main "$@"
