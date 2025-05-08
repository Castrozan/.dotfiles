{ pkgs, ... }:

{
  # Enable gamemode system-wide
  programs.gamemode = {
    enable = true;
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
    nvtop

    # Dependencies for gamemode scripts
    libnotify
  ];

  # Enable Steam with proper gamemode integration
  programs.steam = {
    enable = true;
    remotePlay.openFirewall = true; # Open ports for Steam Remote Play
    dedicatedServer.openFirewall = true; # Open ports for Steam Dedicated Server
    gamescopeSession.enable = true; # Enable gamescope session (separate compositor optimized for gaming)
  };

  # Add environment variables for Steam Proton
  environment.sessionVariables = {
    # Steam Proton paths
    STEAM_EXTRA_COMPAT_TOOLS_PATHS = "\${HOME}/.steam/root/compatibilitytools.d";
    # Force Proton to use NVIDIA
    PROTON_HIDE_NVIDIA_GPU = "0";
    # Enable FSR (FidelityFX Super Resolution) for all games
    WINE_FULLSCREEN_FSR = "1";
    # GameMode integration with Proton
    STEAM_GAMEMODE_LIBRARIES = "${pkgs.gamemode}/lib";
  };
}
