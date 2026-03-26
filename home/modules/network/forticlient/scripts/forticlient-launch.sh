readonly FORTICLIENT_GUI="/opt/forticlient/gui/FortiClient"
readonly FORTICLIENT_SERVICE="forticlient"
readonly WAYLAND_FLAGS=(--ozone-platform=wayland --enable-features=UseOzonePlatform)
readonly SECONDS_TO_WAIT_FOR_GUI_STARTUP=5

_is_gui_running() {
	pgrep -f "${FORTICLIENT_GUI}" >/dev/null 2>&1
}

_is_backend_running() {
	systemctl is-active --quiet "${FORTICLIENT_SERVICE}"
}

_kill_all_gui_processes() {
	pkill -9 -f "FortiClient" 2>/dev/null || true
	pkill -9 -f "fortitray" 2>/dev/null || true
	pkill -9 -f "fortitraylauncher" 2>/dev/null || true
	sleep 1
}

_ensure_backend_is_running() {
	if _is_backend_running; then
		echo "Backend service already running."
	else
		echo "Starting FortiClient backend service..."
		sudo systemctl start "${FORTICLIENT_SERVICE}"
		sleep 2
	fi
}

_launch_gui_with_wayland_flags() {
	"${FORTICLIENT_GUI}" "${WAYLAND_FLAGS[@]}" >/dev/null 2>&1 &
	sleep "${SECONDS_TO_WAIT_FOR_GUI_STARTUP}"
}

_trigger_window_visibility() {
	"${FORTICLIENT_GUI}" 'fabricagent://navPage=vpn' >/dev/null 2>&1
}

main() {
	_ensure_backend_is_running

	if _is_gui_running; then
		echo "FortiClient GUI already running, showing window..."
		_trigger_window_visibility
	else
		echo "Launching FortiClient GUI with Wayland support..."
		_launch_gui_with_wayland_flags
		echo "Triggering window visibility..."
		_trigger_window_visibility
	fi

	echo "FortiClient is ready."
}

main "$@"
