#!/usr/bin/env bash

_shell_runs_inside_a_terminal_multiplexer() {
	[ -n "${TMUX:-}" ] || [ -n "${HERDR_ENV:-}" ]
}

_recover_graphical_session_environment_from_systemd_user_manager() {
	[ -z "${WAYLAND_DISPLAY:-}" ] || return
	command -v systemctl >/dev/null 2>&1 || return

	local imported_environment
	imported_environment=$(systemctl --user show-environment 2>/dev/null) || return
	[ -n "$imported_environment" ] || return

	local variable_name
	for variable_name in WAYLAND_DISPLAY DISPLAY XAUTHORITY XDG_CURRENT_DESKTOP HYPRLAND_INSTANCE_SIGNATURE; do
		[[ $imported_environment =~ (^|$'\n')"$variable_name"=([^$'\n']+) ]] || continue
		export "$variable_name=${BASH_REMATCH[2]}"
	done
}

_fix_stale_hyprland_instance_signature_after_compositor_restart() {
	[ -n "${WAYLAND_DISPLAY:-}" ] || return
	_shell_runs_inside_a_terminal_multiplexer || return
	[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ] || return

	if hyprctl monitors >/dev/null 2>&1; then
		return
	fi

	local hyprland_runtime_directory="/run/user/$(id -u)/hypr"
	[ -d "$hyprland_runtime_directory" ] || return

	local candidate_signature candidate_socket
	for candidate_signature in $(command ls -t "$hyprland_runtime_directory" 2>/dev/null); do
		candidate_socket="$hyprland_runtime_directory/$candidate_signature/.socket.sock"
		[ -S "$candidate_socket" ] || continue
		if HYPRLAND_INSTANCE_SIGNATURE="$candidate_signature" hyprctl monitors >/dev/null 2>&1; then
			export HYPRLAND_INSTANCE_SIGNATURE="$candidate_signature"
			return
		fi
	done
}

case $- in
*i*)
	_recover_graphical_session_environment_from_systemd_user_manager
	_fix_stale_hyprland_instance_signature_after_compositor_restart
	;;
esac
