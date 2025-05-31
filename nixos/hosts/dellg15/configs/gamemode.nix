{ pkgs, lib, ... }:

{
  # Enable gamemode system-wide
  programs.gamemode = {
    enable = true;
    enableRenice = true; # Ensure process priority adjustment is enabled
    settings = {
      general = {
        # Prioritize GPU performance over power savings when gamemode is active
        inhibit_screensaver = true;
        renice = 10; # Higher priority for games
        softrealtime = "auto";
        desktopfile = "steam.desktop"; # For Steam detection
      };

      gpu = {
        # GPU settings for NVIDIA
        apply_gpu_optimisations = true;
        gpu_device = 0; # This will target the NVIDIA GPU
        nv_powermizer_mode = 1; # Maximum performance (0=adaptive, 1=max performance, 2=power saving)
      };

      custom = {
        # Start/end scripts
        start = "${pkgs.libnotify}/bin/notify-send 'GameMode' 'GameMode is now active' -i applications-games";
        end = "${pkgs.libnotify}/bin/notify-send 'GameMode' 'GameMode is no longer active' -i applications-games";
      };
    };
  };

  # Add gamemode-related packages
  environment.systemPackages = with pkgs; [
    # Management tools
    gamemode
    gamescope
    mangohud

    # Add tools for GPU monitoring while gaming
    nvtopPackages.full

    # Dependencies for gamemode scripts
    libnotify

    # Create a wrapper script for running Steam with GameMode properly
    (writeShellScriptBin "steam-gamemode" ''
      #!/usr/bin/env bash
      export LD_PRELOAD="${lib.getLib pkgs.gamemode}/lib/libgamemode.so''${LD_PRELOAD:+:$LD_PRELOAD}"
      exec steam "$@"
    '')
  ];

  # Enable Steam with proper gamemode integration
  programs.steam = {
    enable = true;
    remotePlay.openFirewall = true; # Open ports for Steam Remote Play
    dedicatedServer.openFirewall = true; # Open ports for Steam Dedicated Server
    gamescopeSession.enable = true; # Enable gamescope session (separate compositor optimized for gaming)

    # Fix GameMode integration with Steam
    extraCompatPackages = [
      pkgs.gamemode
    ];
  };

  # Add environment variables for Steam Proton
  environment.sessionVariables = {
    # Steam Proton paths
    STEAM_EXTRA_COMPAT_TOOLS_PATHS = "\${HOME}/.steam/root/compatibilitytools.d";
    # Force Proton to use NVIDIA
    PROTON_HIDE_NVIDIA_GPU = "0";
    # Enable FSR (FidelityFX Super Resolution) for all games
    WINE_FULLSCREEN_FSR = "1";
    # GameMode integration with Proton - Add the specific library path
    STEAM_GAMEMODE_LIBRARIES = "${lib.getLib pkgs.gamemode}/lib";
  };

  # Make the gamemode library available system-wide
  hardware.graphics.extraPackages = [ pkgs.gamemode.lib ];
}
