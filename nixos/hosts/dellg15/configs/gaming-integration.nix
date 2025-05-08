{
  pkgs,
  ...
}:

{
  # Import the game-shift module to ensure it's available
  imports = [
    ../../../modules/game-shift.nix
  ];

  # Create integrated gaming scripts that combine Dell Game Shift with GameMode
  environment.systemPackages = with pkgs; [
    # Enhanced game-run script that activates both Dell Game Shift and GameMode
    (writeShellScriptBin "game-boost" ''
      #!/usr/bin/env bash

      # Check if an argument was provided
      if [ $# -eq 0 ]; then
        echo "Usage: game-boost [command]"
        echo "Runs the specified command with maximum gaming performance:"
        echo "  - Forces NVIDIA GPU usage"
        echo "  - Activates Dell Game Shift hardware mode"
        echo "  - Enables GameMode optimizations"
        exit 1
      fi

      # Activate Dell Game Shift mode
      echo "Activating Dell Game Shift mode..."
      game-shift

      # Check if we're in gaming mode for NVIDIA PRIME
      if [[ "$(readlink /run/current-system)" != *"gaming-mode"* ]]; then
        echo "For maximum performance, consider switching to NVIDIA PRIME sync mode:"
        echo "  $ toggle-gpu-mode"
      fi

      # Run the command with NVIDIA GPU and GameMode
      if command -v gamemoderun &> /dev/null; then
        echo "Running with maximum performance: $@"
        nvidia-offload gamemoderun "$@"
      else
        echo "GameMode not found, running with NVIDIA GPU only: $@"
        nvidia-offload "$@"
      fi
    '')

    # Script to toggle all gaming optimizations on/off
    (writeShellScriptBin "gaming-mode" ''
      #!/usr/bin/env bash

      case "$1" in
        on|ON|start|START)
          # Enable Game Shift
          echo "Enabling Dell Game Shift mode..."
          game-shift
          
          # Check if we're in gaming-mode specialization
          if [[ "$(readlink /run/current-system)" != *"gaming-mode"* ]]; then
            echo "Switching to NVIDIA PRIME sync mode for maximum performance"
            echo "The system will reboot - confirm with y/n:"
            read -p "Proceed with reboot? [y/N] " confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
              sudo /run/current-system/sw/bin/switch-to-configuration test gaming-mode
              echo "Rebooting in 3 seconds..."
              sleep 3
              sudo reboot
            else
              echo "Skipping PRIME sync mode activation (staying in PRIME offload mode)"
            fi
          else
            echo "Already in NVIDIA PRIME sync mode"
          fi
          ;;
          
        off|OFF|stop|STOP)
          # Check if we're in gaming-mode
          if [[ "$(readlink /run/current-system)" == *"gaming-mode"* ]]; then
            echo "Switching back to normal mode (PRIME offload for better battery life)"
            echo "The system will reboot - confirm with y/n:"
            read -p "Proceed with reboot? [y/N] " confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
              sudo /run/current-system/sw/bin/switch-to-configuration switch
              echo "Rebooting in 3 seconds..."
              sleep 3
              sudo reboot
            else
              echo "Skipping PRIME offload mode activation (staying in PRIME sync mode)"
            fi
          else
            echo "Already in normal mode (PRIME offload)"
          fi
          
          # Disable Game Shift (note: game-shift toggles the mode)
          echo "Disabling Dell Game Shift mode..."
          game-shift
          ;;
          
        status|STATUS)
          echo "===== DELL G15 GAMING STATUS ====="
          
          # Game Shift status
          echo -e "\n--- Dell Game Shift Mode ---"
          game-shift
          
          # NVIDIA PRIME mode
          echo -e "\n--- NVIDIA PRIME Mode ---"
          if [[ "$(readlink /run/current-system)" == *"gaming-mode"* ]]; then
            echo "Current mode: Gaming Mode (NVIDIA PRIME sync - maximum performance)"
          else
            echo "Current mode: Normal Mode (PRIME offload - better battery life)"
          fi
          
          # NVIDIA Status
          echo -e "\n--- NVIDIA Status ---"
          nvidia-smi
          
          # Current Renderer
          echo -e "\n--- Current Renderer ---"
          glxinfo | grep "OpenGL renderer" || echo "glxinfo not installed. Install it with: nix-shell -p glxinfo"
          ;;
          
        *)
          echo "Usage: gaming-mode [on|off|status]"
          echo "  on     - Enable all gaming optimizations (Dell Game Shift + NVIDIA PRIME sync)"
          echo "  off    - Disable all gaming optimizations"
          echo "  status - Show current gaming configuration status"
          ;;
      esac
    '')
  ];

  # Create a convenient alias for gaming-mode
  programs.bash.shellAliases = {
    gmode = "gaming-mode";
  };

  # Environment variables for optimal gaming performance
  environment.variables = {
    # Improve Steam performance with NVIDIA
    STEAM_RUNTIME_PREFER_HOST_LIBRARIES = "0";
    # Force discrete NVIDIA GPU for Vulkan applications
    VK_ICD_FILENAMES = "/run/opengl-driver/share/vulkan/icd.d/nvidia_icd.x86_64.json";
  };
}
