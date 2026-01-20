#!/usr/bin/env bash
# Activation script for whisper-input
# Sets up the Python virtualenv and installs dependencies

python_bin="@pythonBin@"
VENV_DIR="$HOME/.local/share/whisper-input/venv"
# No glibc - it breaks system binaries on non-NixOS (and Nix binaries have RPATH)
export LD_LIBRARY_PATH="@portaudio@/lib:@dbusLib@/lib:@ccLib@/lib:${LD_LIBRARY_PATH:-}"
export PKG_CONFIG_PATH="@portaudio@/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export C_INCLUDE_PATH="@portaudio@/include:${C_INCLUDE_PATH:-}"
export LIBRARY_PATH="@portaudio@/lib:${LIBRARY_PATH:-}"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "Setting up whisper-input environment..."
  mkdir -p "$HOME/.local/share/whisper-input"
  "$python_bin" -m venv "$VENV_DIR"
fi

# Always activate and ensure dependencies are installed
# shellcheck disable=SC1091
. "$VENV_DIR/bin/activate"

# Upgrade pip first
pip install --upgrade pip --quiet

# Install/upgrade dependencies (pip will use wheels when available)
# echo "Installing/updating whisper-input dependencies..."

# Install packages that have wheels first
pip install --quiet \
  openai-whisper \
  plyer \
  termcolor || echo "Warning: Some dependencies may have failed"

# Install pynput using evdev-binary (pre-built wheel, avoids source build)
if ! python -c "import pynput" 2>/dev/null; then
  echo "Installing pynput..."
  # First install evdev-binary (pre-built wheel, no compilation needed)
  pip install --quiet evdev-binary || echo "Warning: evdev-binary installation failed"
  # Then install pynput without dependencies (we already have evdev-binary)
  pip install --quiet --no-deps pynput || echo "Warning: pynput installation failed"
  # Install python-xlib which pynput needs
  pip install --quiet python-xlib || echo "Warning: python-xlib installation failed"
fi

# Install beepy and simpleaudio
if ! python -c "import beepy" 2>/dev/null; then
  echo "Installing beepy and simpleaudio..."
  # simpleaudio needs ALSA headers to build
  if ! python -c "import simpleaudio" 2>/dev/null; then
    echo "Building simpleaudio from source (this may take a moment)..."
    export CFLAGS="-I@alsaLibDev@/include ${CFLAGS:-}"
    export LDFLAGS="-L@alsaLib@/lib ${LDFLAGS:-}"
    pip install --quiet simpleaudio || echo "Warning: simpleaudio build failed"
    unset CFLAGS LDFLAGS
  fi
  
  # Install beepy
  pip install --quiet --no-deps "beepy==1.0.9" || echo "Warning: beepy installation failed"
fi

# Install pyaudio separately with build environment set up
# pyaudio needs portaudio to build, ensure it's available
if ! python -c "import pyaudio" 2>/dev/null; then
  echo "Installing pyaudio (this may take a moment as it needs to build)..."
  # Set additional environment variables for building pyaudio
  export CFLAGS="-I@portaudio@/include ${CFLAGS:-}"
  export LDFLAGS="-L@portaudio@/lib ${LDFLAGS:-}"
  pip install --quiet pyaudio || {
    echo "Warning: pyaudio installation failed. You may need to install it manually."
    echo "Try: ~/.local/share/whisper-input/venv/bin/pip install pyaudio"
  }
  unset CFLAGS LDFLAGS
fi

# dbus-python is optional and may fail, install it last
# pip install --quiet dbus-python || echo "Warning: dbus-python installation failed (may not be needed)"
