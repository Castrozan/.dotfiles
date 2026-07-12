# NixOS configuration for zanoni
{
  lib,
  pkgs,
  inputs,
  ...
}:
let
  sshKeys = import ./ssh-keys.nix;
in
{
  imports = [
    ./scripts
    ./secrets.nix
    ./arr-stack.nix
    ./pkgs.nix
    ../../nixos/modules/virtualization.nix
    ../../nixos/modules/fonts.nix
    ../../nixos/modules/steam.nix
    # ../../nixos/modules/media-streaming # Removed: requires insecure qtwebengine-5.15.19
    ../../nixos/modules/agenix.nix
    ../../nixos/modules/nixos-rebuild-guard.nix
    ../../nixos/modules/tailscale.nix
    ../../nixos/modules/man-cache.nix
    ../../nixos/modules/lid-switch.nix
    ../../nixos/modules/sudo.nix
    ../../nixos/modules/mouse-8k-polling.nix
    ../../nixos/modules/home-assistant.nix
    ../../nixos/modules/cockpit-session-bridge
    ../../nixos/modules/cloudflare-tunnel-connector
    ../../nixos/modules/arr-media-tailscale-funnel
    ../../nixos/modules/arr-media-login-ratelimit-proxy
    ../../nixos/modules/arr-stack-on-demand-supervisor
    ../../nixos/modules/jellyseerr-notifications
    ../../nixos/modules/arr-config-provisioner
    ../../nixos/modules/bazarr-auth-provisioner
  ]
  ++ lib.optional (builtins.pathExists ../../private-config/machines/chise/jarvis-connector.nix) ../../private-config/machines/chise/jarvis-connector.nix;

  custom = {
    cockpitSessionBridge = {
      enable = true;
      tmuxEnumerationSocket = "";
    };

    # Disable lid switch suspend for laptop used as server/with external monitor
    lidSwitch.disable = true;
  };

  users.users.zanoni = {
    isNormalUser = true;
    description = "zanoni";
    extraGroups = [
      "networkmanager"
      "wheel"
    ];
    shell = pkgs.bashInteractive;
    openssh.authorizedKeys.keys = sshKeys.authorizedKeys;
  };

  environment = {
    shells = [ pkgs.bashInteractive ];
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
      package = import ../../lib/patched-hyprland.nix { inherit pkgs inputs; };
      portalPackage =
        inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland;
    };
    # Allows running uncompiled binaries from npm, pip and other packages
    nix-ld = {
      enable = true;
      libraries = with pkgs; [
        stdenv.cc.cc
        zlib
        openssl
        curl
        libcap
      ];
    };
  };

  # Services
  services = {
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
    allowedTCPPorts = [
      22
      8123
    ];
  };
}
