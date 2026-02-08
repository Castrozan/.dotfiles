#!/usr/bin/env bash
# Avatar System Shutdown
# Stops all avatar components cleanly

set -euo pipefail

echo "Stopping Avatar System..."

# Stop virtual camera
if pgrep -f 'virtual-camera.js' > /dev/null 2>&1; then
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
if pgrep -f 'avatar/renderer.*next' > /dev/null 2>&1; then
    pkill -f 'avatar/renderer.*next'
    echo "  Renderer stopped"
else
    echo "  Renderer was not running"
fi

# Clean up virtual audio devices
remove_sink() {
    local name=$1
    if XDG_RUNTIME_DIR=/run/user/1000 pactl list sinks short 2>/dev/null | grep -q "$name"; then
        MODULE_ID=$(XDG_RUNTIME_DIR=/run/user/1000 pactl list short modules | grep "$name" | awk '{print $1}')
        if [[ -n "$MODULE_ID" ]]; then
            XDG_RUNTIME_DIR=/run/user/1000 pactl unload-module "$MODULE_ID"
            echo "  $name sink removed"
        fi
    else
        echo "  No $name sink to remove"
    fi
}

# Remove remapped source first (depends on AvatarMic)
remove_module() {
    local name=$1
    MODULE_ID=$(XDG_RUNTIME_DIR=/run/user/1000 pactl list short modules 2>/dev/null | grep "$name" | awk '{print $1}')
    if [[ -n "$MODULE_ID" ]]; then
        XDG_RUNTIME_DIR=/run/user/1000 pactl unload-module "$MODULE_ID"
        echo "  $name removed"
    fi
}

remove_module "AvatarMicSource"
remove_sink "AvatarSpeaker"
remove_sink "AvatarMic"

echo "Avatar system stopped."
