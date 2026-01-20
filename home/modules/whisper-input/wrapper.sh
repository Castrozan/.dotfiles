#!/usr/bin/env bash
# Wrapper script for whisper-input
# Sets up environment and runs the Python script

# Set up ALSA/PulseAudio environment
export ALSA_PLUGIN_DIR="@alsaPlugins@/lib/alsa-lib"

# Add Nix binaries to PATH (avoid glibc conflicts with system binaries)
export PATH="@ffmpeg@/bin:@libnotify@/bin:@wtype@/bin:@wlClipboard@/bin:$PATH"

# Add system libraries needed by PyTorch and other packages (no glibc - breaks system binaries on non-NixOS)
export LD_LIBRARY_PATH="@alsaPlugins@/lib:@pulseaudio@/lib:@portaudio@/lib:@dbusLib@/lib:@ccLib@/lib:${LD_LIBRARY_PATH:-}"

# Use venv managed by home-manager activation
VENV_DIR="$HOME/.local/share/whisper-input/venv"
SCRIPT_DIR="@scriptDir@"

# Try to add pynput and simpleaudio from Nix packages if available (runtime check to avoid build-time evaluation)
# Check common Nix store paths for pynput
for pynput_path in /nix/store/*-python3.11-pynput-*/lib/python3.11/site-packages; do
  if [ -d "$pynput_path" ] && [ -f "$pynput_path/pynput/__init__.py" ]; then
    export PYTHONPATH="$pynput_path:${PYTHONPATH:-}"
    break
  fi
done
# Check for simpleaudio from Nix packages
for simpleaudio_path in /nix/store/*-python3.11-simpleaudio-*/lib/python3.11/site-packages; do
  if [ -d "$simpleaudio_path" ] && [ -f "$simpleaudio_path/simpleaudio/__init__.py" ]; then
    export PYTHONPATH="$simpleaudio_path:${PYTHONPATH:-}"
    break
  fi
done

# Activate venv
if [ -d "$VENV_DIR" ]; then
  # shellcheck disable=SC1091
  . "$VENV_DIR/bin/activate"
else
  echo "Error: whisper-input environment not found. Please run 'home-manager switch' to set it up." >&2
  exit 1
fi

# Run the script
# shellcheck disable=SC2164
cd "$SCRIPT_DIR"
python3 whisper-input.py "$@"
