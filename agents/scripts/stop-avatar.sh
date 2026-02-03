#!/usr/bin/env bash
# Avatar System Shutdown
# Stops all avatar components cleanly

set -euo pipefail

echo "Stopping Avatar System..."

# Stop control server (systemd)
if systemctl --user is-active --quiet avatar-control-server 2>/dev/null; then
    systemctl --user stop avatar-control-server
    echo "  Control server stopped"
else
    echo "  Control server was not running"
fi

# Stop renderer (Next.js dev server)
if pgrep -f 'next-server' > /dev/null 2>&1; then
    pkill -f 'next-server'
    echo "  Renderer stopped"
else
    echo "  Renderer was not running"
fi

# Clean up virtual audio devices
if XDG_RUNTIME_DIR=/run/user/1000 pactl list sinks short 2>/dev/null | grep -q "AvatarSpeaker"; then
    MODULE_ID=$(XDG_RUNTIME_DIR=/run/user/1000 pactl list short modules | grep "AvatarSpeaker" | awk '{print $1}')
    if [[ -n "$MODULE_ID" ]]; then
        XDG_RUNTIME_DIR=/run/user/1000 pactl unload-module "$MODULE_ID"
        echo "  Virtual audio sink removed"
    fi
else
    echo "  No virtual audio sink to remove"
fi

echo "Avatar system stopped."
