#!/usr/bin/env bash
set -Eeuo pipefail

MESSAGE="${1:-Done}"
SEND_MOBILE=false

for arg in "${@:2}"; do
    case "$arg" in
        --mobile) SEND_MOBILE=true ;;
    esac
done

XDG_RUNTIME_DIR="/run/user/$(id -u)"
AUDIO_FILE=$(mktemp /tmp/notify-XXXXXX.mp3)
export XDG_RUNTIME_DIR

cleanup() { rm -f "$AUDIO_FILE"; }
trap cleanup EXIT

edge-tts --voice "en-US-GuyNeural" --text "$MESSAGE" --write-media "$AUDIO_FILE" 2>/dev/null
wpctl set-mute @DEFAULT_AUDIO_SINK@ 0 2>/dev/null || true
mpv --no-video --ao=pulse "$AUDIO_FILE" &>/dev/null

DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus" \
    notify-send -a "Claude Code" "Claude Code" "$MESSAGE" 2>/dev/null || true

if [ "$SEND_MOBILE" = true ]; then
    NTFY_TOPIC="${NTFY_TOPIC:-@notifyTopic@}"
    curl -sf -H "Title: Claude Code" -H "Priority: 3" -d "$MESSAGE" "ntfy.sh/${NTFY_TOPIC}" &>/dev/null || true
fi
