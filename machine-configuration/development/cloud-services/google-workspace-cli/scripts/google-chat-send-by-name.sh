#!/usr/bin/env bash

set -Eeuo pipefail

readonly PINCHTAB_BASE_URL="http://localhost:9867"

main() {
	local recipient_name="${1:-}"
	local message_or_image_path="${2:-}"
	local image_flag="${3:-}"
	local image_path=""
	local message_text=""

	if [[ "$image_flag" == "--image" ]]; then
		image_path="$message_or_image_path"
		_validate_image_arguments "$recipient_name" "$image_path"
	else
		message_text="$message_or_image_path"
		_validate_message_arguments "$recipient_name" "$message_text"
	fi

	_ensure_pinchtab_is_running

	local direct_message_url=""
	direct_message_url=$(_resolve_direct_message_url_by_recipient_name "$recipient_name")

	if [[ -n "$image_path" ]]; then
		google-chat-browser-cli send-image \
			--space-url "$direct_message_url" \
			--image "$image_path"
	else
		google-chat-browser-cli send-message \
			--space-url "$direct_message_url" \
			--message "$message_text"
	fi
}

_validate_message_arguments() {
	local recipient_name="$1"
	local message_text="$2"

	if [[ -z "$recipient_name" || -z "$message_text" ]]; then
		_print_usage
		exit 1
	fi
}

_validate_image_arguments() {
	local recipient_name="$1"
	local image_path="$2"

	if [[ -z "$recipient_name" || -z "$image_path" ]]; then
		_print_usage
		exit 1
	fi

	if [[ ! -f "$image_path" ]]; then
		echo "Error: image file not found: ${image_path}" >&2
		exit 1
	fi
}

_print_usage() {
	echo "usage: google-chat-send-by-name <recipient-name> <message>" >&2
	echo "       google-chat-send-by-name <recipient-name> <image-path> --image" >&2
	echo "  recipient-name: partial or full name to match in chat list" >&2
	echo "  message: text to send" >&2
	echo "  image-path: path to image file (png, jpg, gif, webp)" >&2
}

_ensure_pinchtab_is_running() {
	if ! curl -sf --max-time 2 "${PINCHTAB_BASE_URL}/health" >/dev/null 2>&1; then
		echo "Error: pinchtab is not running at ${PINCHTAB_BASE_URL}" >&2
		exit 1
	fi
}

_resolve_direct_message_url_by_recipient_name() {
	local recipient_name="$1"

	local resolve_json=""
	resolve_json=$(google-chat-browser-cli resolve-contact --name "$recipient_name")

	echo "$resolve_json" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])"
}

main "$@"
