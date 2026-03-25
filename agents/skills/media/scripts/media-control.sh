#!/usr/bin/env bash
set -Eeuo pipefail

DBUS_SESSION_BUS_ADDRESS_DEFAULT="unix:path=/run/user/$(id -u)/bus"
readonly DBUS_SESSION_BUS_ADDRESS_DEFAULT
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-$DBUS_SESSION_BUS_ADDRESS_DEFAULT}"

_show_current_status() {
	local player_name
	player_name=$(playerctl metadata --format '{{playerName}}' 2>/dev/null || echo "none")

	if [[ "$player_name" == "none" ]]; then
		echo "No active media player"
		return
	fi

	local playback_status title artist album position_microseconds length_microseconds
	playback_status=$(playerctl status 2>/dev/null || echo "Unknown")
	title=$(playerctl metadata --format '{{title}}' 2>/dev/null || echo "")
	artist=$(playerctl metadata --format '{{artist}}' 2>/dev/null || echo "")
	album=$(playerctl metadata --format '{{album}}' 2>/dev/null || echo "")
	position_microseconds=$(playerctl position 2>/dev/null || echo "0")
	length_microseconds=$(playerctl metadata --format '{{mpris:length}}' 2>/dev/null || echo "0")

	local position_formatted length_formatted
	position_formatted=$(_format_microseconds_to_timestamp "$position_microseconds")
	length_formatted=$(_format_microseconds_to_timestamp "$length_microseconds")

	echo "Player: $player_name"
	echo "Status: $playback_status"
	[[ -n "$title" ]] && echo "Track: $title"
	[[ -n "$artist" ]] && echo "Artist: $artist"
	[[ -n "$album" ]] && echo "Album: $album"
	echo "Position: $position_formatted / $length_formatted"
}

_format_microseconds_to_timestamp() {
	local microseconds="$1"
	local total_seconds
	total_seconds=$(echo "$microseconds" | awk '{printf "%d", $1/1000000}')
	local minutes=$((total_seconds / 60))
	local seconds=$((total_seconds % 60))
	printf "%d:%02d" "$minutes" "$seconds"
}

_list_active_players() {
	playerctl --list-all 2>/dev/null || echo "No active players"
}

_set_player_volume() {
	local volume_value="$1"
	playerctl volume "$volume_value"
}

_run_playerctl_command() {
	local command="$1"
	shift
	playerctl "$command" "$@"
}

main() {
	local command="${1:-}"
	[[ -z "$command" ]] && {
		echo "Usage: media-control.sh status|play|pause|toggle|next|previous|volume|list" >&2
		exit 1
	}
	shift

	local extra_args=()
	local remaining_args=()
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--player)
			extra_args+=("--player" "$2")
			shift 2
			;;
		*)
			remaining_args+=("$1")
			shift
			;;
		esac
	done

	case "$command" in
	status) _show_current_status ;;
	list) _list_active_players ;;
	play) _run_playerctl_command play "${extra_args[@]}" ;;
	pause) _run_playerctl_command pause "${extra_args[@]}" ;;
	toggle) _run_playerctl_command play-pause "${extra_args[@]}" ;;
	next) _run_playerctl_command next "${extra_args[@]}" ;;
	previous) _run_playerctl_command previous "${extra_args[@]}" ;;
	volume)
		local volume_value="${remaining_args[0]:-}"
		[[ -z "$volume_value" ]] && {
			echo "Usage: media-control.sh volume VALUE [+/-]" >&2
			exit 1
		}
		_set_player_volume "$volume_value"
		;;
	*)
		echo "Unknown command: $command" >&2
		exit 1
		;;
	esac
}

main "$@"
