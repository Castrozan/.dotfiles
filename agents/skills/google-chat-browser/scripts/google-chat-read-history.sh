#!/usr/bin/env bash

set -Eeuo pipefail

readonly PINCHTAB_BASE_URL="http://localhost:9867"
readonly MAX_STABILIZATION_WAIT_SECONDS=10
readonly STABILIZATION_POLL_INTERVAL="0.3"
readonly DEFAULT_MESSAGE_COUNT=10

main() {
	local recipient_name="${1:-}"
	local message_count="${2:-$DEFAULT_MESSAGE_COUNT}"

	_validate_arguments "$recipient_name"
	_ensure_pinchtab_is_running

	local direct_message_url=""
	direct_message_url=$(_resolve_direct_message_url_by_recipient_name "$recipient_name")

	_navigate_to_direct_message "$direct_message_url"
	_print_last_messages "$message_count"
}

_validate_arguments() {
	local recipient_name="$1"

	if [[ -z "$recipient_name" ]]; then
		echo "usage: google-chat-read-history <recipient-name> [message-count]" >&2
		echo "  recipient-name: partial or full name to match in chat list" >&2
		echo "  message-count: number of recent messages to show (default: $DEFAULT_MESSAGE_COUNT)" >&2
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

	local resolve_json=""
	resolve_json=$(google-chat-browser-cli resolve-contact --name "$recipient_name")

	echo "$resolve_json" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])"
}

_navigate_to_direct_message() {
	local direct_message_url="$1"

	curl -sf --max-time 15 -X POST "${PINCHTAB_BASE_URL}/navigate" \
		-H "Content-Type: application/json" \
		-d "{\"url\":\"${direct_message_url}\"}" >/dev/null 2>&1

	sleep 2
	_wait_until_page_stabilizes
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

_print_last_messages() {
	local message_count="$1"

	local raw_page_text=""
	raw_page_text=$(curl -sf --max-time 10 "http://localhost:9867/text" |
		python3 -c "import sys,json; print(json.load(sys.stdin).get('text',''))")

	python3 -c "
import sys, re

raw_text = sys.argv[1]
count = int(sys.argv[2])

message_pattern = re.compile(
    r'((?:Você|[A-ZÀ-Ú][a-zà-ú]+(?: [A-ZÀ-Ú][a-zà-ú]+)*))'
    r',\s*'
    r'((?:\d{1,2}:\d{2}|\d+ (?:min|h|dia|seg)|Agora|Ontem)[^,]*)'
    r',\s*'
    r'(.*?)'
    r'(?:Adicionar reação|A mensagem foi visualizada)',
    re.DOTALL
)

matches = message_pattern.findall(raw_text)

for author, timestamp, body in matches[-count:]:
    clean_body = ' '.join(body.split())
    if clean_body and clean_body not in ('Editada,',):
        prefix = 'Eu' if author == 'Você' else author
        print(f'[{timestamp.strip()}] {prefix}: {clean_body}')
" "$raw_page_text" "$message_count"
}

main "$@"
