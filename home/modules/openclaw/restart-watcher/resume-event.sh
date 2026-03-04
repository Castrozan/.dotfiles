#!/usr/bin/env bash

set -Eeuo pipefail

_send_resume_event() {
	_log "sending system event to wake agents"
	"$OPENCLAW_BIN" system event \
		--mode now \
		--text "$SYSTEM_EVENT_TEXT" \
		--timeout 30000 2>&1 || _log "system event failed (gateway may not be ready)"
}

_handle_gateway_restart() {
	_log "gateway restart detected, waiting for healthy status"

	if _wait_for_gateway_healthy; then
		_log "gateway is healthy, triggering agent resume"
		_send_resume_event
	else
		_log "gateway did not become healthy after $HEALTH_POLL_MAX_ATTEMPTS attempts"
	fi
}
