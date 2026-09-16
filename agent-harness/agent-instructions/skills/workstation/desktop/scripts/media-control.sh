#!/usr/bin/env bash
set -Eeuo pipefail

_is_darwin() {
	[[ "$(uname -s)" == "Darwin" ]]
}

_setup_linux_dbus() {
	local DBUS_SESSION_BUS_ADDRESS_DEFAULT
	DBUS_SESSION_BUS_ADDRESS_DEFAULT="unix:path=/run/user/$(id -u)/bus"
	export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-$DBUS_SESSION_BUS_ADDRESS_DEFAULT}"
}

_darwin_music_status() {
	osascript -e '
		if application "Music" is running then
			tell application "Music"
				set trackName to name of current track
				set trackArtist to artist of current track
				set trackAlbum to album of current track
				set playerState to player state as string
				set pos to player position as integer
				set dur to duration of current track as integer
				return "Player: Music" & linefeed & "Status: " & playerState & linefeed & "Track: " & trackName & linefeed & "Artist: " & trackArtist & linefeed & "Album: " & trackAlbum & linefeed & "Position: " & (pos div 60) & ":" & text -2 thru -1 of ("0" & pos mod 60) & " / " & (dur div 60) & ":" & text -2 thru -1 of ("0" & dur mod 60)
			end tell
		else
			return "No active media player"
		end if
	' 2>/dev/null || echo "No active media player"
}

_darwin_music_command() {
	local command="$1"
	osascript -e "tell application \"Music\" to $command" 2>/dev/null
}

_format_microseconds_to_timestamp() {
	local microseconds="$1"
	local total_seconds
	total_seconds=$(echo "$microseconds" | awk '{printf "%d", $1/1000000}')
	local minutes=$((total_seconds / 60))
	local seconds=$((total_seconds % 60))
	printf "%d:%02d" "$minutes" "$seconds"
}

_linux_show_status() {
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

_linux_list_players() {
	playerctl --list-all 2>/dev/null || echo "No active players"
}

_linux_run_command() {
	local command="$1"
	shift
	playerctl "$command" "$@"
}

_linux_set_volume() {
	playerctl volume "$1"
}

main() {
	local command="${1:-}"
	[[ -z "$command" ]] && {
		echo "Usage: media-control.sh status|play|pause|toggle|next|previous|volume|list" >&2
		exit 1
	}
	shift

	if _is_darwin; then
		case "$command" in
		status) _darwin_music_status ;;
		list) echo "Music" ;;
		play) _darwin_music_command "play" ;;
		pause) _darwin_music_command "pause" ;;
		toggle) _darwin_music_command "playpause" ;;
		next) _darwin_music_command "next track" ;;
		previous) _darwin_music_command "previous track" ;;
		volume)
			local volume_value="${1:-}"
			[[ -z "$volume_value" ]] && {
				echo "Usage: media-control.sh volume VALUE" >&2
				exit 1
			}
			_darwin_music_command "set sound volume to $volume_value"
			;;
		*)
			echo "Unknown command: $command" >&2
			exit 1
			;;
		esac
	else
		_setup_linux_dbus

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
		status) _linux_show_status ;;
		list) _linux_list_players ;;
		play) _linux_run_command play "${extra_args[@]}" ;;
		pause) _linux_run_command pause "${extra_args[@]}" ;;
		toggle) _linux_run_command play-pause "${extra_args[@]}" ;;
		next) _linux_run_command next "${extra_args[@]}" ;;
		previous) _linux_run_command previous "${extra_args[@]}" ;;
		volume)
			local volume_value="${remaining_args[0]:-}"
			[[ -z "$volume_value" ]] && {
				echo "Usage: media-control.sh volume VALUE [+/-]" >&2
				exit 1
			}
			_linux_set_volume "$volume_value"
			;;
		*)
			echo "Unknown command: $command" >&2
			exit 1
			;;
		esac
	fi
}

main "$@"
