#!/usr/bin/env bash

set -Eeuo pipefail

_run_session_cleanup_for_agent() {
	local agent_name="$1"
	_log "running session cleanup for agent=$agent_name"
	"$OPENCLAW_BIN" sessions cleanup --agent "$agent_name" --enforce 2>&1 || _log "session cleanup failed for agent=$agent_name"
}
