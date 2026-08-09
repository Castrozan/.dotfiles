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
    ../../../media/arr-stack/chise/chise-arr-stack-nixos.nix
    ./pkgs.nix
    ../../../development/virtualization/virtualization-nixos.nix
    ../../../desktop/fonts/fonts-nixos.nix
    ../../../gaming/steam/steam-nixos.nix
    # ../../../media/media-streaming/media-streaming-nixos.nix # Removed: requires insecure qtwebengine-5.15.19
    ../../../security/secrets/agenix-nixos.nix
    ../../../development/system-rebuild/nixos-rebuild-guard-nixos.nix
    ../../../network/tailscale/tailscale-nixos.nix
    ../../../network/vpn/nordvpn/wgnord-dns-priority-over-tailscale-nixos.nix
    ../../../network/vpn/nordvpn/wgnord-tailnet-route-preservation-nixos.nix
    ../../../operating-system/manual-pages/man-cache-nixos.nix
    ../../../operating-system/power-management/lid-switch-nixos.nix
    ../../../security/privilege-escalation/sudo-nixos.nix
    ../../../desktop/mouse/mouse-polling-rate-nixos.nix
    ../../../home-automation/home-assistant/home-assistant-nixos.nix
    ../../../terminal/workspace-manager/cockpit-session-bridge/cockpit-session-bridge-nixos.nix
    ../../../network/cloudflare-tunnel-connector/cloudflare-tunnel-connector-nixos.nix
    ../../../media/arr-stack/tailscale-funnel/arr-media-tailscale-funnel-nixos.nix
    ../../../media/arr-stack/login-rate-limit-proxy/arr-media-login-ratelimit-proxy-nixos.nix
    ../../../media/arr-stack/on-demand-supervisor/arr-stack-on-demand-supervisor-nixos.nix
    ../../../media/arr-stack/jellyseerr-notifications/jellyseerr-notifications-nixos.nix
    ../../../media/arr-stack/configuration/arr-config-provisioner-nixos.nix
    ../../../media/arr-stack/bazarr-auth/bazarr-auth-provisioner-nixos.nix
    ../../../media/arr-stack/jellyfin-library-access/jellyfin-library-access-provisioner-nixos.nix
    ../../../media/arr-stack/jellyfin-subtitle-extraction/jellyfin-subtitle-extraction-warmer-nixos.nix
    ../../../media/arr-stack/kavita-library-access/kavita-library-access-provisioner-nixos.nix
    ../../../media/arr-stack/jellyseerr-account-permissions/jellyseerr-account-permission-provisioner-nixos.nix
    ../../../media/arr-stack/jellyseerr-private-request-routing/jellyseerr-private-request-routing-provisioner-nixos.nix
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
      package = import ../../../../machine-configuration/desktop/hyprland/patched-hyprland.nix {
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
