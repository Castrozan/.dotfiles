#!/usr/bin/env bash

_fix_stale_hyprland_instance_signature_after_compositor_restart() {
	[ -n "${WAYLAND_DISPLAY:-}" ] || return
	[ -n "${TMUX:-}" ] || return
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
*i*) _fix_stale_hyprland_instance_signature_after_compositor_restart ;;
esac
