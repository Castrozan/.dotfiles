{
  pkgs,
  lib,
  username,
  nixpkgs-version,
  ...
}:
{
  imports = [
    ./nvidia.nix
    ./libinput-quirks.nix
    ../scripts
    ../../../nixos/modules/xdg-portal.nix
  ];

  # Bootloader and kernel
  boot = {
    loader = {
      systemd-boot.enable = true;
      efi.canTouchEfiVariables = true;
    };
    kernel.sysctl."vm.swappiness" = 80;
  };

  # Override filesystem configuration with labels for resilience
  # This prevents UUID mismatch issues during GPT corruption recovery
  # https://chatgpt.com/share/68e1bfff-f1d0-800e-b971-24f822d1c93b
  # For new machines: Run `./bin/setup-filesystem-labels` after NixOS installation
  # to create the required labels, then rebuild with this configuration.
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

  # Nix configuration
  nix = {
    settings = {
      # Enable experimental features
      experimental-features = [
        "nix-command"
        "flakes"
      ];

      # Binary caches - huge win for build speed
      substituters = [
        "https://cache.nixos.org"
        "https://nix-community.cachix.org"
      ];
      trusted-public-keys = [
        "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
        "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
      ];

      # Parallelism - use all CPU cores
      max-jobs = "auto";
      cores = 0; # use all cores

      # Download optimization - increase buffer and parallel downloads
      download-buffer-size = "524288000"; # 500 MiB
      http-connections = 50; # More parallel downloads (default is 1)

      # Eval cache - faster repeated rebuilds
      eval-cache = true;

      # Sandbox and store optimization
      sandbox = true;
      auto-optimise-store = true;

      # Allow the user to run nix commands
      trusted-users = [ username ];
    };

    # Automatic store optimization - runs nix-store --optimise to hard-link identical files
    # Reduces disk space usage by deduplicating identical files in the store
    # Runs weekly when system is active (systemd timer will run when PC is on)
    optimise = {
      automatic = true;
      dates = [ "weekly" ];
    };

    # Garbage collection
    gc = {
      automatic = lib.mkDefault true;
      dates = lib.mkDefault "weekly";
      options = lib.mkDefault "--delete-older-than 7d";
    };
  };

  # Allow unfree packages
  nixpkgs.config.allowUnfree = true;

  # Disable man-cache generation
  documentation.man.generateCaches = false;

  # This value determines the NixOS release from which the default
  # settings for stateful data, like file locations and database versions
  # on your system were taken. It's perfectly fine and recommended to leave
  # this value at the release version of the first install of this system.
  # Before changing this value read the documentation for this option
  # (e.g. man configuration.nix or on https://nixos.org/nixos/options.html).
  system.stateVersion = nixpkgs-version; # Did you read the comment?

  swapDevices = [
    {
      device = "/swapfile";
      size = 8192; # 8 GiB
    }
  ];

  # Networking
  networking = {
    hostName = "nixos";
    networkmanager.enable = true;
  };

  time.timeZone = "America/Sao_Paulo";

  # Internationalization
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

  # Programs
  programs = {
    dconf.enable = true;
    command-not-found.enable = false;
  };

  # Console keymap
  console.keyMap = "br-abnt2";

  # Security
  security.rtkit.enable = true;

  # XDG Portal for screen sharing (Hyprland + GNOME coexistence)
  custom.xdgPortal.enable = true;

  # Services
  services = {
    # X11 and GNOME
    xserver = {
      enable = true;
      xkb = {
        layout = "br";
        variant = "nodeadkeys";
      };
    };
    displayManager.gdm.enable = true;
    desktopManager.gnome.enable = true;

    # Printing
    printing.enable = true;

    # Sound with pipewire
    pulseaudio.enable = false;
    pipewire = {
      enable = true;
      alsa = {
        enable = true;
        support32Bit = true;
      };
      pulse.enable = true;
    };

    # Touchpad support
    libinput = {
      enable = true;
      # Dell G15 5515 touchpad configuration
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

    # Custom udev rules for Dell G15 5515 touchpad
    udev.extraRules = builtins.readFile ./udev-rules/99-dell-g15-touchpad.rules;
  };

  # Additional packages for hardware monitoring and management
  environment.systemPackages = with pkgs; [
    lm_sensors
    i2c-tools
    powertop
    mesa-demos
    vulkan-tools
    pciutils
    usbutils
  ];
}
