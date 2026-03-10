#!/usr/bin/env bash

set -Eeuo pipefail

readonly PINCHTAB_BASE_URL="http://localhost:9867"
readonly GOOGLE_CHAT_HOME_URL="https://chat.google.com/"
readonly MAX_STABILIZATION_WAIT_SECONDS=10
readonly STABILIZATION_POLL_INTERVAL="0.3"

main() {
	local recipient_name="${1:-}"
	local message_text="${2:-}"

	_validate_arguments "$recipient_name" "$message_text"
	_ensure_pinchtab_is_running

	local direct_message_url=""
	direct_message_url=$(_resolve_direct_message_url_by_recipient_name "$recipient_name")

	google-chat-browser-cli send-message \
		--space-url "$direct_message_url" \
		--message "$message_text"
}

_validate_arguments() {
	local recipient_name="$1"
	local message_text="$2"

	if [[ -z "$recipient_name" || -z "$message_text" ]]; then
		echo "usage: google-chat-send-by-name <recipient-name> <message>" >&2
		echo "  recipient-name: partial or full name to match in chat list" >&2
		echo "  message: text to send" >&2
		exit 1
	fi
}

_ensure_pinchtab_is_running() {
	if ! curl -sf --max-time 2 "${PINCHTAB_BASE_URL}/health" >/dev/null 2>&1; then
		echo "Error: pinchtab is not running at ${PINCHTAB_BASE_URL}" >&2
		exit 1
	fi
}

_resolve_direct_message_url_by_recipient_name() {
	local recipient_name="$1"

	_navigate_to_google_chat_home
	_wait_until_page_stabilizes

	local interactive_snapshot=""
	interactive_snapshot=$(_capture_interactive_snapshot)

	local matching_element_ref=""
	matching_element_ref=$(_find_contact_ref_in_snapshot "$interactive_snapshot" "$recipient_name")

	if [[ -z "$matching_element_ref" ]]; then
		_expand_direct_messages_section
		interactive_snapshot=$(_capture_interactive_snapshot)
		matching_element_ref=$(_find_contact_ref_in_snapshot "$interactive_snapshot" "$recipient_name")
	fi

	if [[ -z "$matching_element_ref" ]]; then
		echo "Error: no contact matching '${recipient_name}' found in chat list" >&2
		exit 1
	fi

	_click_element_and_extract_url "$matching_element_ref"
}

_navigate_to_google_chat_home() {
	curl -sf --max-time 15 -X POST "${PINCHTAB_BASE_URL}/navigate" \
		-H "Content-Type: application/json" \
		-d "{\"url\":\"${GOOGLE_CHAT_HOME_URL}\"}" >/dev/null 2>&1
}

_wait_until_page_stabilizes() {
	local elapsed_seconds=0
	local previous_snapshot=""
	local current_snapshot=""

	sleep 1

	while (($(echo "$elapsed_seconds < $MAX_STABILIZATION_WAIT_SECONDS" | bc -l))); do
		current_snapshot=$(curl -sf --max-time 10 \
			"${PINCHTAB_BASE_URL}/snapshot?diff=true&format=compact" 2>/dev/null || echo "")

		if [[ -n "$previous_snapshot" && "$current_snapshot" == "$previous_snapshot" ]]; then
			return 0
		fi

		previous_snapshot="$current_snapshot"
		sleep "$STABILIZATION_POLL_INTERVAL"
		elapsed_seconds=$(echo "$elapsed_seconds + $STABILIZATION_POLL_INTERVAL" | bc -l)
	done
}

_capture_interactive_snapshot() {
	curl -sf --max-time 15 \
		"${PINCHTAB_BASE_URL}/snapshot?filter=interactive&format=compact"
}

_find_contact_ref_in_snapshot() {
	local snapshot_text="$1"
	local search_name="$2"

	local matching_ref=""
	matching_ref=$(echo "$snapshot_text" | while IFS= read -r snapshot_line; do
		if [[ "$snapshot_line" != *":link "* ]]; then
			continue
		fi

		local lowercase_line=""
		lowercase_line=$(echo "$snapshot_line" | tr '[:upper:]' '[:lower:]')

		if [[ "$lowercase_line" != *"pressione a tecla tab"* ]]; then
			continue
		fi

		if _all_search_words_match_line "$search_name" "$lowercase_line"; then
			echo "$snapshot_line" | grep -oP '^e\d+' || true
			break
		fi
	done)

	echo "$matching_ref"
}

_all_search_words_match_line() {
	local search_name="$1"
	local lowercase_line="$2"

	local search_word=""
	for search_word in $(echo "$search_name" | tr '[:upper:]' '[:lower:]'); do
		if [[ "$lowercase_line" != *"$search_word"* ]]; then
			return 1
		fi
	done

	return 0
}

_expand_direct_messages_section() {
	local snapshot_text=""
	snapshot_text=$(_capture_interactive_snapshot)

	local expand_button_ref=""
	expand_button_ref=$(echo "$snapshot_text" | grep -i "mostrar tudo.*mensagens diretas" | grep -oP '^e\d+' || true)

	if [[ -n "$expand_button_ref" ]]; then
		curl -sf --max-time 10 -X POST "${PINCHTAB_BASE_URL}/action" \
			-H "Content-Type: application/json" \
			-d "{\"kind\":\"click\",\"ref\":\"${expand_button_ref}\"}" >/dev/null 2>&1
		sleep 1
		_wait_until_page_stabilizes
	fi
}

_click_element_and_extract_url() {
	local element_ref="$1"

	curl -sf --max-time 10 -X POST "${PINCHTAB_BASE_URL}/action" \
		-H "Content-Type: application/json" \
		-d "{\"kind\":\"click\",\"ref\":\"${element_ref}\"}" >/dev/null 2>&1

	sleep 1
	_wait_until_page_stabilizes

	local page_snapshot=""
	page_snapshot=$(curl -sf --max-time 10 \
		"${PINCHTAB_BASE_URL}/snapshot?format=compact&depth=0" 2>/dev/null || echo "")

	local page_url=""
	page_url=$(echo "$page_snapshot" | head -1 | grep -oP 'https://chat\.google\.com/[^ |]+' || true)

	if [[ -z "$page_url" ]]; then
		echo "Error: could not extract DM URL after clicking contact" >&2
		exit 1
	fi

	echo "$page_url"
}

main "$@"
