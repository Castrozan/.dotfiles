#!/usr/bin/env bash

set -Eeuo pipefail

_send_timeout_system_event() {
	local agent_name="$1"
	local error_message="$2"

	local event_text="LLM timeout detected for agent ${agent_name}: ${error_message}. Session was cleaned up automatically. If the agent is unresponsive, send /new to start a fresh session."

	_log "sending system event for timeout recovery"
	"$OPENCLAW_BIN" system event \
		--mode now \
		--text "$event_text" \
		--timeout 30000 2>&1 || _log "system event send failed"
}
