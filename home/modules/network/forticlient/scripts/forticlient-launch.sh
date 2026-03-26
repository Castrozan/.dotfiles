#!/usr/bin/env bash
set -Eeuo pipefail

readonly FORTICLIENT_GUI="/opt/forticlient/gui/FortiClient"
readonly FORTICLIENT_SERVICE="forticlient"
readonly WAYLAND_FLAGS=(--ozone-platform=wayland --enable-features=UseOzonePlatform)
readonly SECONDS_TO_WAIT_FOR_GUI_STARTUP=5

_kill_all_gui_processes() {
	pkill -9 -f "FortiClient" 2>/dev/null || true
	pkill -9 -f "fortitray" 2>/dev/null || true
	pkill -9 -f "fortitraylauncher" 2>/dev/null || true
	sleep 1
}

_restart_backend_service() {
	sudo systemctl restart "${FORTICLIENT_SERVICE}"
	sleep 2
}

_launch_gui_with_wayland_flags() {
	"${FORTICLIENT_GUI}" "${WAYLAND_FLAGS[@]}" >/dev/null 2>&1 &
	sleep "${SECONDS_TO_WAIT_FOR_GUI_STARTUP}"
}

_trigger_window_visibility() {
	"${FORTICLIENT_GUI}" 'fabricagent://navPage=vpn' >/dev/null 2>&1
}

main() {
	echo "Stopping existing FortiClient GUI processes..."
	_kill_all_gui_processes

	echo "Restarting FortiClient backend service..."
	_restart_backend_service

	echo "Launching FortiClient GUI with Wayland support..."
	_launch_gui_with_wayland_flags

	echo "Triggering window visibility..."
	_trigger_window_visibility

	echo "FortiClient is ready."
}

main "$@"
