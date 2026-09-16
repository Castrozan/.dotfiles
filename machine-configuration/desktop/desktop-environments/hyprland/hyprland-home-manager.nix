{ lib, ... }:
{
  imports = [
    ./session/graphical-services-activation.nix
    ./hyprland-packages-home-manager.nix
    ./appearance/mouse-pointer-theme-home-manager.nix
    ./appearance/hyprland-theme-home-manager.nix
    ./hyprland-command-packages-home-manager.nix
    ./session/wlogout.nix
    ./session/wayland-electron.nix
    ../quickshell/bar/quickshell-bar-home-manager.nix

    ./wlr-which-key.nix
    ./mako.nix
    ../quickshell/window-switcher/quickshell-window-switcher-home-manager.nix
    ../quickshell/overview/quickshell-overview-home-manager.nix
    ../../screen-capture/satty-home-manager.nix
    ../../../audio/wiremix-home-manager.nix
    ./session/xdg-desktop-portal-hyprland-service.nix
    ./session/focus-daemon-service.nix
    ../../applications/launcher/fuzzel-home-manager.nix
  ];

  home = {
    file.".config/hypr".source = ./program-configuration;

    activation.ensureMonitorOverrideFile = lib.hm.dag.entryBefore [ "writeBoundary" ] ''
      touch "$HOME/.cache/hypr-monitors-override.conf"
    '';
  };

  xdg.configFile."hypr-host/monitors.conf".text = lib.mkDefault "";
  xdg.configFile."hypr-host/input.conf".text = lib.mkDefault "";
}
