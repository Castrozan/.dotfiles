#!/usr/bin/env bash
# Avatar System Shutdown
# Stops all avatar components cleanly

set -euo pipefail

XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export XDG_RUNTIME_DIR

echo "Stopping Avatar System..."

# Stop virtual camera
if pgrep -f 'virtual-camera.js' >/dev/null 2>&1; then
	pkill -f 'virtual-camera.js'
	echo "  Virtual camera stopped"
else
	echo "  Virtual camera was not running"
fi

# Stop control server (systemd)
if systemctl --user is-active --quiet avatar-control-server 2>/dev/null; then
	systemctl --user stop avatar-control-server
	echo "  Control server stopped"
else
	echo "  Control server was not running"
fi

# Stop renderer (Next.js dev server)
if pgrep -f 'skills/avatar/renderer.*next' >/dev/null 2>&1; then
	pkill -f 'skills/avatar/renderer.*next'
	echo "  Renderer stopped"
else
	echo "  Renderer was not running"
fi

python3 "$(dirname "$0")/browser/runtime.py" stop
echo "  Avatar browser stopped"

# Remove virtual audio devices
for sink in AvatarSpeaker AvatarMic AvatarMicSource; do
	module_id=$(pactl list modules short 2>/dev/null | grep "sink_name=$sink " | awk '{print $1}')
	if [ -n "$module_id" ]; then
		pactl unload-module "$module_id"
		echo "  $sink removed"
	fi
done

# Re-enable hey-bot keyword detection
rm -f "${XDG_RUNTIME_DIR:-$HOME/.local/state}/hey-bot/keywords-disabled"
echo "Avatar system stopped."
