# NixOS configuration for zanoni
{
  lib,
  pkgs,
  inputs,
  ...
}:
let
  bashrc = builtins.readFile ../../.bashrc;
  sshKeys = import ./ssh-keys.nix;
in
{
  imports = [
    ./scripts
    ./pkgs.nix
    ../../nixos/modules/virtualization.nix
    ../../nixos/modules/fonts.nix
    ../../nixos/modules/steam.nix
    ../../nixos/modules/whisper-cpp.nix
    # ../../nixos/modules/media-streaming # Removed: requires insecure qtwebengine-5.15.19
    ../../nixos/modules/agenix.nix
    ../../nixos/modules/tailscale.nix
    ../../nixos/modules/man-cache.nix
    ../../nixos/modules/lid-switch.nix
    ../../nixos/modules/sudo.nix
  ];

  # Disable lid switch suspend for laptop used as server/with external monitor
  custom.lidSwitch.disable = true;

  users.users.zanoni = {
    isNormalUser = true;
    description = "zanoni";
    extraGroups = [
      "networkmanager"
      "wheel"
    ];
    shell = pkgs.fish;
    openssh.authorizedKeys.keys = sshKeys.authorizedKeys;
  };

  # Global Bash configuration
  # TODO: this is workaround from home/packages/bash.nix
  environment = {
    etc."bashrc".text = bashrc;
    # NIX_PATH configuration
    # Decision: Keep default NIX_PATH for compatibility with nix repl and other tools
    # For flake-based workflows, use `nix repl '<nixpkgs>'` or import from flake inputs directly
    # Reference: https://github.com/NixOS/nix/issues/9574
    variables = {
      NIX_PATH = lib.mkDefault "nixpkgs=/nix/var/nix/profiles/per-user/root/channels/nixos";
      # Force Qt applications to use Wayland
      QT_QPA_PLATFORM = "wayland";
    };
  };

  # Programs
  programs = {
    # Screen locker - needs NixOS-level enable for DRM/PAM permissions
    hyprlock.enable = true;
    # NOTE: programs.hyprlock pulls in hypridle. We don't want auto-lock,
    # so hypridle.service is masked via ~/.config/systemd/user/hypridle.service -> /dev/null
    # More hyprland configuration in home/hyprland.nix
    hyprland = {
      enable = true;
      xwayland.enable = true;
      package = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland;
      portalPackage =
        inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland;
    };
    # Enable fish globally so it's registered in /etc/shells and available as a login shell
    fish.enable = true;
    # Allows running uncompiled binaries from npm, pip and other packages
    nix-ld = {
      enable = true;
      libraries = with pkgs; [
        stdenv.cc.cc
        zlib
        openssl
        curl
      ];
    };
  };

  # Security - gnome-keyring PAM integration for Hyprland
  security.pam.services.gdm.enableGnomeKeyring = true;

  # Services
  services = {
    # Gnome-keyring for password/secrets storage (used by browsers, etc.)
    gnome.gnome-keyring.enable = true;
    flatpak.enable = true;
    openssh = {
      enable = true;
      settings = {
        PermitRootLogin = "no";
        PubkeyAuthentication = true;
      };
    };
  };

  networking.firewall = {
    enable = true;
    allowedTCPPorts = [ 22 ];
  };

  age = {
    identityPaths = [
      "/home/zanoni/.ssh/id_ed25519"
    ];
    secrets = {
      "id_ed25519_phone" = {
        file = ../../secrets/id_ed25519_phone.age;
        owner = "zanoni";
        mode = "600";
      };
      "openclaw-gateway-token" = {
        file = ../../secrets/openclaw-gateway-token.age;
        owner = "zanoni";
        mode = "400";
      };
      "telegram-bot-token" = {
        file = ../../secrets/telegram-bot-token.age;
        owner = "zanoni";
        mode = "400";
      };
      "nvidia-api-key" = {
        file = ../../secrets/nvidia-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "id_ed25519_workpc" = {
        file = ../../secrets/id_ed25519_workpc.age;
        owner = "zanoni";
        mode = "600";
      };
      "grid-token-robson" = {
        file = ../../secrets/grid-token-robson.age;
        owner = "zanoni";
        mode = "400";
      };
      "grid-token-clever" = {
        file = ../../secrets/grid-token-clever.age;
        owner = "zanoni";
        mode = "400";
      };
      "brave-api-key" = {
        file = ../../secrets/brave-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "tavily-api-key" = {
        file = ../../secrets/tavily-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "grid-hosts" = {
        file = ../../secrets/grid-hosts.age;
        owner = "zanoni";
        mode = "400";
      };
    };
  };
}
