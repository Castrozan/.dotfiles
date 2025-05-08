{ pkgs, ... }:

{
  environment.systemPackages = with pkgs; [
    # Add a convenient script for nvidia-offload
    (writeShellScriptBin "nvidia-offload" ''
      export __NV_PRIME_RENDER_OFFLOAD=1
      export __NV_PRIME_RENDER_OFFLOAD_PROVIDER=NVIDIA-G0
      export __GLX_VENDOR_LIBRARY_NAME=nvidia
      export __VK_LAYER_NV_optimus=NVIDIA_only
      exec "$@"
    '')

    # Add a script to toggle between gaming mode and regular mode
    (writeShellScriptBin "toggle-gpu-mode" ''
      #!/usr/bin/env bash

      # Check if we're in gaming mode
      if [[ "$(readlink /run/current-system)" == *"gaming-mode"* ]]; then
        echo "Switching to normal mode (PRIME offload - better battery life)"
        sudo /run/current-system/sw/bin/switch-to-configuration switch
      else
        echo "Switching to gaming mode (NVIDIA PRIME sync - better performance)"
        sudo /run/current-system/sw/bin/switch-to-configuration test gaming-mode
      fi

      echo "System will reboot in 5 seconds. Press Ctrl+C to cancel."
      sleep 5
      sudo reboot
    '')

    # Add a script to check current GPU status
    (writeShellScriptBin "gpu-status" ''
      #!/usr/bin/env bash

      echo "===== GPU Mode ====="
      if [[ "$(readlink /run/current-system)" == *"gaming-mode"* ]]; then
        echo "Current mode: Gaming Mode (NVIDIA PRIME sync)"
      else
        echo "Current mode: Normal Mode (PRIME offload)"
      fi

      echo -e "\n===== NVIDIA Status ====="
      nvidia-smi

      echo -e "\n===== Current Renderer ====="
      glxinfo | grep "OpenGL renderer" || echo "glxinfo not installed. Install it with: nix-shell -p glxinfo"
    '')

    # Add a simple benchmark tool to test GPU performance
    (writeShellScriptBin "test-gpu" ''
      #!/usr/bin/env bash

      if ! command -v glxgears &> /dev/null; then
        echo "glxgears not found. Installing mesa-demos temporarily..."
        nix-shell -p mesa-demos --run "glxgears -info"
      else
        glxgears -info
      fi
    '')

    # Add a script to run games with the NVIDIA GPU
    (writeShellScriptBin "game-run" ''
      #!/usr/bin/env bash

      # Check if an argument was provided
      if [ $# -eq 0 ]; then
        echo "Usage: game-run [command]"
        echo "Runs the specified command using the NVIDIA GPU with GameMode enabled"
        exit 1
      fi

      # Run the command with NVIDIA GPU and GameMode
      if command -v gamemoderun &> /dev/null; then
        echo "Running with NVIDIA GPU and GameMode: $@"
        nvidia-offload gamemoderun "$@"
      else
        echo "GameMode not installed. Running with NVIDIA GPU only: $@"
        nvidia-offload "$@"
      fi
    '')
  ];

  # Environment variables for better NVIDIA support
  environment.variables = {
    # Force DRI_PRIME for NVIDIA (needed for some applications)
    DRI_PRIME = "1";
  };
}
