#!/usr/bin/env bash
set -Eeuo pipefail

readonly DBUS_BUS_PATH="unix:path=/run/user/$(id -u)/bus"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-$DBUS_BUS_PATH}"

_status() {
	playerctl metadata --format '{{artist}} - {{title}} [{{status}}]'
}

_volume() {
	local value="$1"
	if [[ "$value" =~ ^\+([0-9]+)$ ]]; then
		wpctl set-volume @DEFAULT_AUDIO_SINK@ "${BASH_REMATCH[1]}%+"
	elif [[ "$value" =~ ^-([0-9]+)$ ]]; then
		wpctl set-volume @DEFAULT_AUDIO_SINK@ "${BASH_REMATCH[1]}%-"
	elif [[ "$value" =~ ^([0-9]+)$ ]]; then
		local pct="${BASH_REMATCH[1]}"
		wpctl set-volume @DEFAULT_AUDIO_SINK@ "$(awk "BEGIN {printf \"%.2f\", $pct/100}")"
	else
		echo "Usage: media-control.sh volume VALUE  (0-100 or +N/-N)" >&2
		exit 1
	fi
}

main() {
	local cmd="${1:-}"
	[[ -z "$cmd" ]] && {
		echo "Usage: media-control.sh play|pause|toggle|next|prev|status|volume VALUE" >&2
		exit 1
	}
	shift

	case "$cmd" in
	play) playerctl play ;;
	pause) playerctl pause ;;
	toggle) playerctl play-pause ;;
	next) playerctl next ;;
	prev) playerctl previous ;;
	status) _status ;;
	volume)
		local val="${1:-}"
		[[ -z "$val" ]] && {
			echo "Usage: media-control.sh volume VALUE" >&2
			exit 1
		}
		_volume "$val"
		;;
	*)
		echo "Unknown command: $cmd" >&2
		exit 1
		;;
	esac
}

main "$@"
