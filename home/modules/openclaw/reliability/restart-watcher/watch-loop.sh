#!/usr/bin/env bash

set -Eeuo pipefail

_send_startup_resume_event() {
	_log "watcher started with gateway already running, sending resume event"
	_handle_gateway_restart
}

_watch_for_restarts() {
	_log "watching $GATEWAY_SERVICE for restart events"

	_wait_for_gateway_service
	_send_startup_resume_event

	local previous_active_enter_timestamp=""
	previous_active_enter_timestamp=$(_get_gateway_active_enter_timestamp)
	local gateway_was_down=false

	while true; do
		sleep "$POLL_INTERVAL_SECONDS"

		if ! _is_gateway_active; then
			if [ "$gateway_was_down" = false ]; then
				_log "gateway went down, restarting"
				gateway_was_down=true
				_restart_gateway_service
			fi
			continue
		fi

		local current_active_enter_timestamp
		current_active_enter_timestamp=$(_get_gateway_active_enter_timestamp)

		if [ "$gateway_was_down" = true ]; then
			_log "gateway came back up after being down"
			gateway_was_down=false
			_handle_gateway_restart
		elif [ "$current_active_enter_timestamp" != "$previous_active_enter_timestamp" ] &&
			[ -n "$previous_active_enter_timestamp" ]; then
			_handle_gateway_restart
		fi

		previous_active_enter_timestamp="$current_active_enter_timestamp"
	done
}

main() {
	_watch_for_restarts
}
