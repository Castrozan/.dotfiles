#!/usr/bin/env bash
set -Eeuo pipefail

_is_darwin() {
	[[ "$(uname -s)" == "Darwin" ]]
}

_ensure_wayland_environment() {
	export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
	export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
}

_darwin_read() {
	local mime_type="$1"
	if [[ -z "$mime_type" || "$mime_type" == text/* ]]; then
		pbpaste
		return
	fi
	local osascript_clipboard_class
	local file_extension
	case "$mime_type" in
	image/png)
		osascript_clipboard_class="«class PNGf»"
		file_extension="png"
		;;
	image/tiff)
		osascript_clipboard_class="«class TIFF»"
		file_extension="tiff"
		;;
	*)
		echo "Unsupported MIME type on darwin: $mime_type (supported: image/png, image/tiff, text/*)" >&2
		exit 1
		;;
	esac
	local output="/tmp/clipboard-$(date +%Y%m%d-%H%M%S).${file_extension}"
	osascript \
		-e "set clipboard_image_bytes to the clipboard as ${osascript_clipboard_class}" \
		-e "set output_file_handle to open for access POSIX file \"$output\" with write permission" \
		-e "set eof of output_file_handle to 0" \
		-e "write clipboard_image_bytes to output_file_handle" \
		-e "close access output_file_handle" >/dev/null 2>&1
	echo "$output"
}

_darwin_write() {
	local content="$1"
	printf '%s' "$content" | pbcopy
}

_darwin_write_stdin() {
	pbcopy
}

_linux_read() {
	local mime_type="$1"
	if [[ -z "$mime_type" ]]; then
		wl-paste --no-newline 2>/dev/null || echo ""
	elif [[ "$mime_type" == image/* ]]; then
		local ext="${mime_type#image/}"
		if [[ ! "$ext" =~ ^[a-zA-Z0-9+.-]+$ ]]; then
			echo "Invalid image type: $mime_type" >&2
			exit 1
		fi
		local output="/tmp/clipboard-$(date +%Y%m%d-%H%M%S).${ext}"
		wl-paste --type "$mime_type" >"$output" 2>/dev/null
		echo "$output"
	else
		wl-paste --type "$mime_type" 2>/dev/null || echo ""
	fi
}

_linux_write() {
	local content="$1"
	echo -n "$content" | wl-copy
}

_linux_write_typed() {
	local mime_type="$1"
	local content="$2"
	echo -n "$content" | wl-copy --type "$mime_type"
}

_linux_write_typed_stdin() {
	local mime_type="$1"
	wl-copy --type "$mime_type"
}

_linux_watch() {
	wl-paste --watch cat
}

main() {
	local subcommand="${1:-}"
	if [[ -z "$subcommand" ]]; then
		echo "Usage: clipboard.sh read|write|watch [--type MIME] [text]" >&2
		exit 1
	fi
	shift

	if ! _is_darwin; then
		_ensure_wayland_environment
	fi

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
		if _is_darwin; then
			_darwin_read "$mime_type"
		else
			_linux_read "$mime_type"
		fi
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
		if _is_darwin; then
			if [[ ${#positional[@]} -gt 0 ]]; then
				_darwin_write "${positional[0]}"
			elif ! [[ -t 0 ]]; then
				_darwin_write_stdin
			else
				echo "Usage: clipboard.sh write \"text\"  OR  echo text | clipboard.sh write" >&2
				exit 1
			fi
		else
			if [[ -n "$mime_type" ]] && [[ ${#positional[@]} -gt 0 ]]; then
				_linux_write_typed "$mime_type" "${positional[0]}"
			elif [[ -n "$mime_type" ]]; then
				_linux_write_typed_stdin "$mime_type"
			elif [[ ${#positional[@]} -gt 0 ]]; then
				_linux_write "${positional[0]}"
			elif ! [[ -t 0 ]]; then
				wl-copy
			else
				echo "Usage: clipboard.sh write \"text\"  OR  echo text | clipboard.sh write" >&2
				exit 1
			fi
		fi
		;;
	watch)
		if _is_darwin; then
			echo "watch is not implemented on macOS" >&2
			exit 1
		fi
		_linux_watch
		;;
	*)
		echo "Unknown subcommand: $subcommand. Use read, write, or watch." >&2
		exit 1
		;;
	esac
}

main "$@"
