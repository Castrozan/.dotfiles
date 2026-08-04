{
  config,
  lib,
  username,
  ...
}:
{
  assertions = [
    {
      assertion = builtins.elem "flakes" config.nix.settings.experimental-features;
      message = "Flakes must be enabled — this entire dotfiles repository is structured as a flake; disabling flakes breaks all rebuilds, CI, and development workflows";
    }
    {
      assertion = config.nix.settings.max-jobs <= 6;
      message = "max-jobs must be <= 6 — with 16GB RAM, more than 6 parallel build jobs causes memory pressure that makes the desktop unusable (laggy compositor, input delay, swap thrashing). Tested: max-jobs=auto (12) saturated all RAM even with memory caps";
    }
    {
      assertion = config.nix.settings.cores <= 2;
      message = "cores must be <= 2 — each build job spawns compiler processes across this many cores. With max-jobs=6 and cores=2, builds use at most 12 core-slots leaving headroom for interactive processes. cores=0 (all) caused 100% CPU saturation during rebuilds";
    }
    {
      assertion = config.nix.daemonCPUSchedPolicy == "batch";
      message = "nix-daemon must use batch CPU scheduling — batch scheduling tells the kernel these are throughput-oriented background tasks, ensuring interactive processes (compositor, terminal, browser) always preempt build jobs for CPU time";
    }
    {
      assertion = config.nix.daemonIOSchedClass == "idle";
      message = "nix-daemon must use idle IO scheduling — idle class means build IO only happens when no interactive IO is pending, preventing rebuilds from starving disk reads for applications and file cache";
    }
    {
      assertion = config.systemd.services.nix-daemon.serviceConfig.Nice == 19;
      message = "nix-daemon must run at Nice=19 — lowest CPU priority ensures interactive processes always get scheduled first, preventing the desktop lag that occurs when 6 compiler jobs compete with the compositor at equal priority";
    }
  ];

  nix = {
    settings = {
      experimental-features = [
        "nix-command"
        "flakes"
      ];

      substituters = [
        "https://cache.nixos.org"
        "https://nix-community.cachix.org"
        "https://hyprland.cachix.org"
        "https://devenv.cachix.org"
      ];
      trusted-public-keys = [
        "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
        "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
        "hyprland.cachix.org-1:a7pgxzMz7+chwVL3/pzj6jIBMioiJM7ypFP8PwtkuGc="
        "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw="
      ];

      max-jobs = 6;
      cores = 2;

      download-buffer-size = "524288000";
      http-connections = 50;

      eval-cache = true;

      sandbox = true;
      auto-optimise-store = true;

      trusted-users = [ username ];
    };

    daemonCPUSchedPolicy = "batch";
    daemonIOSchedClass = "idle";
    daemonIOSchedPriority = 4;

    optimise = {
      automatic = true;
      dates = [ "weekly" ];
    };

    gc = {
      automatic = lib.mkDefault true;
      dates = lib.mkDefault "weekly";
      options = lib.mkDefault "--delete-older-than 7d";
    };
  };

  systemd.services.nix-daemon.serviceConfig.Nice = 19;
}
