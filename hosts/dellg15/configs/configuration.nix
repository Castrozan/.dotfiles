{
  config,
  pkgs,
  lib,
  username,
  nixpkgs-version,
  ...
}:
{
  assertions = [
    {
      assertion = config.zramSwap.enable;
      message = "zram swap is required — with only 16GB RAM and heavy Nix builds, zram provides compressed swap in memory that is 3-5x faster than disk swap and prevents OOM kills during parallel compilation";
    }
    {
      assertion = config.services.earlyoom.enable;
      message = "earlyoom is required — without proactive OOM killing the kernel OOM killer activates too late, freezing the desktop for 30+ seconds before killing a random process instead of the actual memory hog";
    }
    {
      assertion = config.boot.kernel.sysctl."vm.swappiness" >= 100;
      message = "High swappiness (>=100) is required — with zram enabled, swappiness above 100 tells the kernel to prefer compressing pages into zram over evicting file cache, which keeps build artifacts cached and improves rebuild speed";
    }
    {
      assertion = builtins.elem "flakes" config.nix.settings.experimental-features;
      message = "Flakes must be enabled — this entire dotfiles repository is structured as a flake; disabling flakes breaks all rebuilds, CI, and development workflows";
    }
  ];

  imports = [
    ./audio.nix
    ./nvidia.nix
    ./libinput-quirks.nix
    ./keyboard-backlight.nix
    ../scripts
    ../../../nixos/modules/xdg-portal.nix
    ../../../nixos/modules/openclaw-watchdog.nix
    ../../../nixos/modules/network-optimization.nix
  ];

  boot = {
    loader = {
      systemd-boot.enable = true;
      efi.canTouchEfiVariables = true;
    };
    kernel.sysctl."vm.swappiness" = 150;

    extraModulePackages = [ config.boot.kernelPackages.v4l2loopback ];
    kernelModules = [ "v4l2loopback" ];
    extraModprobeConfig = ''
      options v4l2loopback devices=1 video_nr=10 card_label="Avatar Cam" exclusive_caps=1
    '';
  };

  fileSystems = lib.mkForce {
    "/" = {
      device = "/dev/disk/by-label/nixos-root";
      fsType = "ext4";
    };
    "/boot" = {
      device = "/dev/disk/by-label/NIXOS_BOOT";
      fsType = "vfat";
      options = [
        "fmask=0022"
        "dmask=0022"
      ];
    };
  };

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
      ];
      trusted-public-keys = [
        "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
        "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
        "hyprland.cachix.org-1:a7pgxzMz7+chwVL3/pzj6jIBMioiJM7ypFP8PwtkuGc="
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

  nixpkgs.config.allowUnfree = true;

  documentation.man.generateCaches = false;

  system.stateVersion = nixpkgs-version;

  zramSwap = {
    enable = true;
    memoryPercent = 50;
    algorithm = "zstd";
  };

  swapDevices = [
    {
      device = "/swapfile";
      size = 4096;
    }
  ];

  services.earlyoom = {
    enable = true;
    freeMemThreshold = 10;
    freeSwapThreshold = 15;
    freeMemKillThreshold = 5;
    freeSwapKillThreshold = 5;
    enableNotifications = true;
    extraArgs = [
      "-r"
      "3600"
      "--avoid"
      "(^|/)(init|Xorg|Xwayland|sshd|systemd)$"
      "--prefer"
      "(^|/)(nix|nix-build|cc1plus|rustc|node|java|chrome_crashpad|claude)$"
    ];
  };

  networking = {
    hostName = "nixos";
    networkmanager.enable = true;
  };

  time.timeZone = "America/Sao_Paulo";

  i18n = {
    defaultLocale = "en_US.UTF-8";
    extraLocaleSettings = {
      LC_ADDRESS = "pt_BR.UTF-8";
      LC_IDENTIFICATION = "pt_BR.UTF-8";
      LC_MEASUREMENT = "pt_BR.UTF-8";
      LC_MONETARY = "pt_BR.UTF-8";
      LC_NAME = "pt_BR.UTF-8";
      LC_NUMERIC = "pt_BR.UTF-8";
      LC_PAPER = "pt_BR.UTF-8";
      LC_TELEPHONE = "pt_BR.UTF-8";
      LC_TIME = "pt_BR.UTF-8";
    };
  };

  programs = {
    dconf.enable = true;
    command-not-found.enable = false;
    ssh.enableAskPassword = false;
  };

  console.keyMap = "br-abnt2";

  custom.xdgPortal.enable = true;

  services = {
    xserver = {
      enable = true;
      xkb = {
        layout = "br";
        variant = "nodeadkeys";
      };
    };
    displayManager.gdm.enable = true;
    desktopManager.gnome.enable = true;

    printing.enable = true;

    libinput = {
      enable = true;
      touchpad = {
        accelSpeed = "0.6";
        accelProfile = "adaptive";
        naturalScrolling = false;
        tapping = true;
        clickMethod = "clickfinger";
        disableWhileTyping = true;
        additionalOptions = ''
          Option "PalmDetection" "1"
          Option "TappingDragLock" "1"
          Option "Sensitivity" "0.8"
        '';
      };
    };

    udev.extraRules = builtins.readFile ./udev-rules/99-dell-g15-touchpad.rules;

    openclaw-watchdog = {
      enable = true;
      interval = 30;
      gatewayPort = 18789;
      user = username;
    };
  };

  environment.systemPackages = with pkgs; [
    lm_sensors
    i2c-tools
    powertop
    mesa-demos
    vulkan-tools
    pciutils
    usbutils
    v4l-utils
    ffmpeg-full
  ];
}
