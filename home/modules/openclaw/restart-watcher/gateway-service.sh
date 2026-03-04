#!/usr/bin/env bash

set -Eeuo pipefail

_is_gateway_active() {
	$SYSTEMCTL_CMD --user is-active "$GATEWAY_SERVICE" >/dev/null 2>&1
}

_get_gateway_active_enter_timestamp() {
	$SYSTEMCTL_CMD --user show "$GATEWAY_SERVICE" \
		--property=ActiveEnterTimestamp --value 2>/dev/null || echo ""
}

_restart_gateway_service() {
	_log "gateway is down, restarting $GATEWAY_SERVICE"
	$SYSTEMCTL_CMD --user start "$GATEWAY_SERVICE" 2>&1 || _log "failed to start $GATEWAY_SERVICE"
}

_wait_for_gateway_service() {
	_log "waiting for $GATEWAY_SERVICE to become active"
	while true; do
		if _is_gateway_active; then
			_log "$GATEWAY_SERVICE is active"
			return 0
		fi
		sleep "$POLL_INTERVAL_SECONDS"
	done
}
