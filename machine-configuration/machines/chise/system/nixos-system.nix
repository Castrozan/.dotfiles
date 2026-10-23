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
    ./media/arr-stack.nix
    ../../../media/container-resources/media-container-resources-nixos.nix
    ./pkgs.nix
    ../../../development/virtualization/virtualization-nixos.nix
    ../../../development/testing/python-interpreter-nixos.nix
    ../../../desktop/appearance/fonts/fonts-nixos.nix
    ../../../gaming/steam/steam-nixos.nix
    ../../../media/media-streaming/stremio-streaming-server-nixos.nix
    ../../../media/media-streaming/stremio-comet-nixos.nix
    ../../../media/media-streaming/stremio-public-origin-nixos.nix
    ../../../security/secrets/agenix-nixos.nix
    ../../../development/system-rebuild/nixos-rebuild-guard-nixos.nix
    ../../../network/vpn/protonvpn/protonvpn-nixos.nix
    ../../../network/tailscale/tailscale-nixos.nix
    ../../../operating-system/manual-pages/man-cache-nixos.nix
    ../../../operating-system/power-management/lid-switch-nixos.nix
    ../../../security/privilege-escalation/sudo-nixos.nix
    ../../../desktop/input/mouse/mouse-polling-rate-nixos.nix
    ../../../home-automation/home-assistant/home-assistant-nixos.nix
    ../../../terminal/workspace-manager/cockpit-session-bridge/cockpit-session-bridge-nixos.nix
    ../../../network/cloudflare-tunnel-connector/cloudflare-tunnel-connector-nixos.nix
  ]
  ++ lib.optional (builtins.pathExists ../../../../private-configuration/machines/chise/jarvis-connector.nix) ../../../../private-configuration/machines/chise/jarvis-connector.nix;

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
      package = import ../../../desktop/desktop-environments/hyprland/build/patched-hyprland.nix {
        inherit pkgs inputs;
      };
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
    tailscale = {
      useRoutingFeatures = "server";
      extraSetFlags = [ "--advertise-exit-node" ];
      openFirewall = true;
    };
    resolved = {
      enable = true;
      extraConfig = ''
        DNSStubListenerExtra=100.94.11.81
        DNSStubListenerExtra=172.17.0.1
      '';
    };
    openssh = {
      enable = true;
      settings = {
        PermitRootLogin = "no";
        PubkeyAuthentication = true;
      };
    };
  };

  networking.networkmanager.ensureProfiles.profiles.zanoni-5ghz = {
    ipv4 = {
      method = "auto";
      route-metric = 50;
      dns-priority = -50;
    };
    ipv6 = {
      method = "auto";
      route-metric = 50;
      dns-priority = -50;
    };
  };

  virtualisation.docker.daemon.settings.dns = [ "172.17.0.1" ];

  networking.firewall = {
    interfaces = {
      docker0 = {
        allowedTCPPorts = [ 53 ];
        allowedUDPPorts = [ 53 ];
      };
      "br-+" = {
        allowedTCPPorts = [ 53 ];
        allowedUDPPorts = [ 53 ];
      };
    };
    enable = true;
    allowedTCPPorts = [
      22
    ];
  };
}
