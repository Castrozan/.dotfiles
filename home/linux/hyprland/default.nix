{ lib, ... }:
{
  imports = [
    ./graphical-services-activation.nix
    ./packages.nix
    ./cursor.nix
    ./themes.nix
    ./scripts.nix
    ./wlogout.nix
    ./wayland-electron.nix
    ./quickshell/bar.nix

    ./wlr-which-key.nix
    ./mako.nix
    ./quickshell/window-switcher.nix
    ./quickshell/overview.nix
    ../desktop/satty.nix
    ../audio/wiremix.nix
    ./xdg-desktop-portal-hyprland-service.nix
    ./focus-daemon-service.nix
    ../desktop/fuzzel.nix
  ];

  home = {
    file.".config/hypr".source = ../../../.config/hypr;

    activation.ensureMonitorOverrideFile = lib.hm.dag.entryBefore [ "writeBoundary" ] ''
      touch "$HOME/.cache/hypr-monitors-override.conf"
    '';
  };

  xdg.configFile."hypr-host/monitors.conf".text = lib.mkDefault "";
  xdg.configFile."hypr-host/input.conf".text = lib.mkDefault "";
}
