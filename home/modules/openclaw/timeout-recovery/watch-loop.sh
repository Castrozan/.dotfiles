#!/usr/bin/env bash

set -Eeuo pipefail

_is_duplicate_within_cooldown() {
	local agent_name="$1"
	local cooldown_file="${COOLDOWN_DIR}/${agent_name}"

	if [ -f "$cooldown_file" ]; then
		local last_recovery_epoch
		last_recovery_epoch=$(cat "$cooldown_file")
		local now_epoch
		now_epoch=$(date +%s)
		local elapsed_seconds=$((now_epoch - last_recovery_epoch))

		if [ "$elapsed_seconds" -lt "$COOLDOWN_SECONDS" ]; then
			_log "skipping recovery for agent=$agent_name (cooldown: ${elapsed_seconds}s < ${COOLDOWN_SECONDS}s)"
			return 0
		fi
	fi
	return 1
}

_record_recovery_timestamp() {
	local agent_name="$1"
	mkdir -p "$COOLDOWN_DIR"
	date +%s >"${COOLDOWN_DIR}/${agent_name}"
}

_handle_timeout_error() {
	local log_line="$1"

	local agent_name
	agent_name=$(_extract_agent_name_from_lane_error "$log_line")

	if [ -z "$agent_name" ]; then
		_log "timeout detected but could not extract agent name from: $log_line"
		return
	fi

	if _is_duplicate_within_cooldown "$agent_name"; then
		return
	fi

	_log "timeout detected for agent=$agent_name"
	_record_recovery_timestamp "$agent_name"
	_run_session_cleanup_for_agent "$agent_name"
	_send_timeout_system_event "$agent_name" "LLM request timed out"
}

_monitor_gateway_logs() {
	_log "monitoring gateway logs for timeout errors"

	journalctl --user -u "$GATEWAY_SERVICE" -f --no-pager -o cat 2>/dev/null | while IFS= read -r line; do
		if echo "$line" | grep -q "FailoverError: LLM request timed out"; then
			_handle_timeout_error "$line"
		fi
	done
}

main() {
	_monitor_gateway_logs
}
