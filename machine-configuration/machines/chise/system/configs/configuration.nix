{
  config,
  pkgs,
  lib,
  nixpkgs-version,
  ...
}:
{
  imports = [
    ./audio.nix
    ./nvidia.nix
    ./libinput-quirks.nix
    ./keyboard-backlight.nix
    ./nix-daemon.nix
    ./memory-pressure.nix
    ../scripts
    ../../../../../nixos/modules/xdg-portal.nix
    ../../../../../nixos/modules/network-optimization.nix
  ];

  boot = {
    loader = {
      systemd-boot.enable = true;
      efi.canTouchEfiVariables = true;
    };

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
    "/home/zanoni/arr-stack/data" = {
      device = "/dev/disk/by-label/arr-data";
      fsType = "ext4";
      options = [
        "nofail"
        "x-systemd.device-timeout=10s"
      ];
    };
  };

  nixpkgs.config.allowUnfree = true;

  documentation.man.generateCaches = false;

  system.stateVersion = nixpkgs-version;

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
