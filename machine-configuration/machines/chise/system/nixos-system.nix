{
  config,
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
    ./home-assistant.nix
    ./media/arr-stack.nix
    ../../../media/container-resources/media-container-resources-nixos.nix
    ./pkgs.nix
    ../../../development/virtualization/virtualization-nixos.nix
    ../../../development/testing/python-interpreter-nixos.nix
    ../../../desktop/appearance/fonts/fonts-nixos.nix
    ../../../gaming/horizon/horizon-nixos.nix
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
    ../../../security/certificate-trust/certificate-bundle-environment-nixos.nix
    ../../../desktop/input/mouse/mouse-polling-rate-nixos.nix
    ../../../terminal/workspace-manager/cockpit-session-bridge/cockpit-session-bridge-nixos.nix
    ../../../network/cloudflare-tunnel-connector/cloudflare-tunnel-connector-nixos.nix
  ]
  ++ lib.optional (builtins.pathExists ../../../../private-configuration/machines/chise/jarvis-connector.nix) ../../../../private-configuration/machines/chise/jarvis-connector.nix;

  custom = {
    cockpitSessionBridge = {
      enable = true;
      tmuxEnumerationSocket = "";
    };

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
    variables = {
      NIX_PATH = lib.mkDefault "nixpkgs=/nix/var/nix/profiles/per-user/root/channels/nixos";
      QT_QPA_PLATFORM = "wayland";
    };
  };

  programs = {
    hyprlock.enable = true;
    hyprland = {
      enable = true;
      xwayland.enable = true;
      withUWSM = true;
      package = import ../../../desktop/desktop-environments/hyprland/build/patched-hyprland.nix {
        inherit pkgs inputs;
      };
      portalPackage =
        inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland;
    };
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

  security.pam.services.greetd.enableGnomeKeyring = true;

  boot = {
    consoleLogLevel = 3;
    initrd.verbose = false;
    kernelParams = [
      "quiet"
      "udev.log_level=3"
      "systemd.show_status=error"
    ];
  };

  systemd.services.greetd.serviceConfig = {
    Type = "idle";
    StandardError = "journal";
  };

  services = {
    greetd = {
      enable = true;
      settings.default_session.command = lib.concatStringsSep " " [
        (lib.getExe pkgs.tuigreet)
        "--time"
        "--remember"
        "--asterisks"
        "--cmd"
        "'${lib.getExe config.programs.uwsm.package} start -F -- ${config.programs.hyprland.package}/bin/start-hyprland'"
      ];
    };
    flatpak.enable = true;
    hypridle.enable = lib.mkForce false;
    tailscale = {
      useRoutingFeatures = "server";
      extraSetFlags = [ "--advertise-exit-node" ];
      openFirewall = true;
    };
    resolved = {
      enable = true;
      settings.Resolve.DNSStubListenerExtra = [
        "100.94.11.81"
        "172.17.0.1"
      ];
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
