#!/usr/bin/env bash

set -Eeuo pipefail

_extract_agent_name_from_lane_error() {
	local log_line="$1"
	echo "$log_line" | grep -oP 'lane=session:agent:\K[^:]+' || echo ""
}
