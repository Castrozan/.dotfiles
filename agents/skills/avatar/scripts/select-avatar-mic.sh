#!/usr/bin/env bash
# Select AvatarMic for browser via CDP
# Use when avatar needs to speak in Meet/calls without changing system default

set -e

BROWSER_PORT="${PW_PORT:-9222}"
AVATAR_MIC="Avatar_Microphone"

echo "Selecting AvatarMic via CDP for browser on port $BROWSER_PORT..."

# Get list of audio devices and find Avatar_Microphone
DEVICES=$(curl -s "http://localhost:$BROWSER_PORT/json/list" 2>/dev/null | jq -r '.[0].webSocketDebuggerUrl' 2>/dev/null)

if [ -z "$DEVICES" ] || [ "$DEVICES" = "null" ]; then
    echo "Error: Chrome DevTools not available on port $BROWSER_PORT"
    echo "Make sure agent browser is running with --remote-debugging-port=$BROWSER_PORT"
    exit 1
fi

# Use wscat or similar to send CDP commands to select AvatarMic
# This is a placeholder - actual implementation needs WebSocket client
# Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/

# TODO: Implement CDP SetAudioCaptureState with deviceId
# Media.setAudioCaptureState or emulate media devices

echo "Selected AvatarMic via CDP (placeholder implementation)"
echo "For now, manually select 'Avatar_Microphone' in Meet settings"