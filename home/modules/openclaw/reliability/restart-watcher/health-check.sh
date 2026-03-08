#!/usr/bin/env bash

set -Eeuo pipefail

_wait_for_gateway_healthy() {
	local attempt=0
	while [ "$attempt" -lt "$HEALTH_POLL_MAX_ATTEMPTS" ]; do
		if "$CURL_BIN" -sf "http://localhost:${GATEWAY_PORT}/health" >/dev/null 2>&1; then
			return 0
		fi
		attempt=$((attempt + 1))
		sleep "$HEALTH_POLL_INTERVAL_SECONDS"
	done
	return 1
}
