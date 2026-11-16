#!/usr/bin/env bash
set -euo pipefail

launch_agent_label="$1"
package_runtime_root_path="$2"
launch_agent_plist_path="$3"
launch_agent_domain="gui/$(id -u)"
launch_agent_target="$launch_agent_domain/$launch_agent_label"

if ! launchctl print "$launch_agent_target" >/dev/null 2>&1; then
	launchctl enable "$launch_agent_target"
	launchctl bootstrap "$launch_agent_domain" "$launch_agent_plist_path"
	exit 0
fi

if [[ -L "$package_runtime_root_path" ]]; then
	exit 0
fi

launchctl kickstart -k "$launch_agent_target"
