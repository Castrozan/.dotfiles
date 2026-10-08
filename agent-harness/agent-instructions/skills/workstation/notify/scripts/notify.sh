#!/usr/bin/env bash
set -Eeuo pipefail

MESSAGE="${1:-Done}"
SEND_MOBILE=false

shift || true
while [[ $# -gt 0 ]]; do
	case "$1" in
	--mobile)
		SEND_MOBILE=true
		shift
		;;
	*) shift ;;
	esac
done

XDG_RUNTIME_DIR="/run/user/$(id -u)"
export XDG_RUNTIME_DIR

DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus" \
	notify-send -h int:suppress-sound:1 -a "Claude Code" "Claude Code" "$MESSAGE" &>/dev/null || true

if [[ "$SEND_MOBILE" == true ]]; then
	NTFY_TOPIC="${NTFY_TOPIC:-@notifyTopic@}"
	curl -sf -H "Title: Claude Code" -H "Priority: 3" -d "$MESSAGE" "ntfy.sh/${NTFY_TOPIC}" &>/dev/null || true
fi
