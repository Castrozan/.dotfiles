#!/usr/bin/env bash
# Avatar System Shutdown
# Stops all avatar components cleanly

set -euo pipefail

XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export XDG_RUNTIME_DIR

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
if pgrep -f 'skills/avatar/renderer.*next' > /dev/null 2>&1; then
    pkill -f 'skills/avatar/renderer.*next'
    echo "  Renderer stopped"
else
    echo "  Renderer was not running"
fi

# Clean up virtual audio devices
remove_sink() {
    local name=$1
    if pactl list sinks short 2>/dev/null | grep -q "$name"; then
        MODULE_ID=$(pactl list short modules | grep "$name" | awk '{print $1}')
        if [[ -n "$MODULE_ID" ]]; then
            pactl unload-module "$MODULE_ID"
            echo "  $name sink removed"
        fi
    else
        echo "  No $name sink to remove"
    fi
}

# Remove remapped source first (depends on AvatarMic)
remove_module() {
    local name=$1
    MODULE_ID=$(pactl list short modules 2>/dev/null | grep "$name" | awk '{print $1}')
    if [[ -n "$MODULE_ID" ]]; then
        pactl unload-module "$MODULE_ID"
        echo "  $name removed"
    fi
}

remove_module "AvatarMicSource"
remove_sink "AvatarSpeaker"
remove_sink "AvatarMic"

# Stop agent browser (prevents stale headless instance on next start)
if pgrep -f 'remote-debugging-port=9222' > /dev/null 2>&1; then
    pkill -f 'pinchtab' 2>/dev/null || true
    pkill -f 'remote-debugging-port=9222' 2>/dev/null || true
    echo "  Agent browser stopped"
else
    echo "  Agent browser was not running"
fi

# Re-enable hey-bot keyword detection
rm -f /tmp/hey-bot-keywords-disabled
echo "Avatar system stopped."
