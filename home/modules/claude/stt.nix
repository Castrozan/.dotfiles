# Claude STT (Speech-to-Text) build dependencies
#
# Provides native build dependencies for the claude-stt plugin which installs
# via pip into a venv. The plugin needs to compile:
# - evdev (requires linux kernel headers)
# - sounddevice (requires portaudio)
# - numpy and other native extensions
#
# After rebuild, run the claude-stt setup: /claude-stt:setup
{ pkgs, lib, ... }:
let
  # Runtime libraries needed by native Python extensions (numpy, etc.)
  runtimeLibs = with pkgs; [
    stdenv.cc.cc.lib  # libstdc++.so.6
    portaudio         # libportaudio.so
    zlib              # libz.so (numpy dependency)
  ];

  runtimeLibPath = lib.makeLibraryPath runtimeLibs;

  # Build dependencies for claude-stt python packages
  buildDeps = with pkgs; [
    # Python with venv support
    python312

    # For sounddevice (audio capture)
    portaudio

    # For evdev (keyboard/mouse input handling)
    linuxHeaders

    # Build essentials
    gcc
    pkg-config
    gnumake
  ] ++ runtimeLibs;

  # Wrapper script to run claude-stt setup with correct environment
  claude-stt-setup = pkgs.writeShellScriptBin "claude-stt-setup" ''
    set -e

    PLUGIN_ROOT="$HOME/.claude/plugins/cache/jarrodwatts-claude-stt/claude-stt/0.1.0"

    if [ ! -d "$PLUGIN_ROOT" ]; then
      echo "Error: claude-stt plugin not found at $PLUGIN_ROOT"
      echo "Install the plugin first via Claude Code: /install-plugin jarrodwatts/claude-stt"
      exit 1
    fi

    echo "Setting up claude-stt with NixOS build environment..."

    # Set up build environment for native extensions
    export C_INCLUDE_PATH="${pkgs.linuxHeaders}/include:${pkgs.portaudio}/include:''${C_INCLUDE_PATH:-}"
    export LIBRARY_PATH="${pkgs.portaudio}/lib:''${LIBRARY_PATH:-}"
    export LD_LIBRARY_PATH="${runtimeLibPath}:''${LD_LIBRARY_PATH:-}"
    export PKG_CONFIG_PATH="${pkgs.portaudio}/lib/pkgconfig:''${PKG_CONFIG_PATH:-}"

    # Run the setup script
    cd "$PLUGIN_ROOT"
    ${pkgs.python312}/bin/python scripts/setup.py "$@"

    echo ""
    echo "claude-stt setup complete!"
    echo "Start the daemon with: /claude-stt:start"
  '';
in
{
  home.packages = buildDeps ++ [ claude-stt-setup ];

  # Environment variables for building native Python extensions
  home.sessionVariables = {
    # Make kernel headers available for evdev compilation
    C_INCLUDE_PATH = "${pkgs.linuxHeaders}/include:${pkgs.portaudio}/include";

    # Runtime library path for native extensions (libstdc++, portaudio, zlib)
    # Required for numpy, sounddevice, and other compiled Python packages
    LD_LIBRARY_PATH = runtimeLibPath;
  };
}
