#!/usr/bin/env bash
# Setup script for Hey Cleber voice assistant
# Creates the Python venv with all dependencies

set -euo pipefail

VENV_DIR="${HOME}/.local/share/hey-cleber-venv"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Hey Cleber Setup ==="
echo ""

# Step 1: Create venv
if [ -d "$VENV_DIR" ]; then
    echo "Venv already exists at $VENV_DIR"
    echo "To recreate, run: rm -rf $VENV_DIR && $0"
else
    echo "Creating Python venv at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

# Step 2: Install dependencies
echo "Installing Python packages..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel 2>&1 | tail -1

pip install \
    numpy \
    sounddevice \
    requests \
    openwakeword \
    edge-tts \
    2>&1 | tail -5

echo ""
echo "Installed packages:"
pip list 2>/dev/null | grep -iE "numpy|sounddevice|requests|openwakeword|edge.tts|onnx"

# Step 3: Download openwakeword models
echo ""
echo "Pre-downloading openwakeword models..."
python3 -c "
from openwakeword.model import Model
m = Model(wakeword_models=['hey_jarvis'])
print('Model loaded successfully!')
print('Available models:', list(m.models.keys()))
"

# Step 4: Install systemd service
echo ""
echo "Installing systemd user service..."
mkdir -p "${HOME}/.config/systemd/user"
cat > "${HOME}/.config/systemd/user/hey-cleber.service" << EOF
[Unit]
Description=Hey Cleber Voice Assistant
After=pipewire.service pipewire-pulse.service
Wants=pipewire.service

[Service]
Type=simple
ExecStart=/bin/bash -c 'export CLAWDBOT_GATEWAY_TOKEN=\$(cat /run/agenix/openclaw-gateway-token); exec ${VENV_DIR}/bin/python3 ${SCRIPT_DIR}/hey-cleber.py --wake-word hey_jarvis --threshold 0.5'
Restart=on-failure
RestartSec=5
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=HOME=/home/zanoni
Environment=CLAWDBOT_GATEWAY_URL=http://localhost:@gatewayPort@
Environment=WHISPER_BIN=/run/current-system/sw/bin/whisper
Environment=MPV_BIN=/run/current-system/sw/bin/mpv
Environment=PATH=/run/current-system/sw/bin:/etc/profiles/per-user/zanoni/bin:/usr/bin:/bin
# PortAudio needs this for sounddevice
Environment=LD_LIBRARY_PATH=/nix/store/xm08aqdd7pxcdhm0ak6aqb1v7hw5q6ri-gcc-14.3.0-lib/lib:/nix/store/yil5gzi7sxmx5jn90883daa4rj03bf8b-home-manager-path/lib

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hey-cleber

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
echo "Service installed. Commands:"
echo "  systemctl --user start hey-cleber     # Start"
echo "  systemctl --user stop hey-cleber      # Stop"
echo "  systemctl --user enable hey-cleber    # Auto-start on login"
echo "  journalctl --user -u hey-cleber -f    # View logs"

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Quick test:"
echo "  source $VENV_DIR/bin/activate"
echo "  python3 ${SCRIPT_DIR}/hey-cleber.py --list-devices"
echo "  python3 ${SCRIPT_DIR}/hey-cleber.py --debug"
