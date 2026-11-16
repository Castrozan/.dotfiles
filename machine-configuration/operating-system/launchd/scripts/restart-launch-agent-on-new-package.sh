#!/usr/bin/env bash
set -euo pipefail

launch_agent_label="$1"
package_runtime_root_path="$2"
launch_agent_target="gui/$(id -u)/$launch_agent_label"

if [[ -L "$package_runtime_root_path" ]]; then
	exit 0
fi

if ! launchctl print "$launch_agent_target" >/dev/null 2>&1; then
	exit 0
fi

launchctl kickstart -k "$launch_agent_target"
