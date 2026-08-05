{ lib, ... }:
{
  imports = [
    ./graphical-services-activation.nix
    ./hyprland-packages-home-manager.nix
    ./mouse-pointer-theme-home-manager.nix
    ./hyprland-theme-home-manager.nix
    ./hyprland-command-packages-home-manager.nix
    ./wlogout.nix
    ./wayland-electron.nix
    ../quickshell/bar/quickshell-bar-home-manager.nix

    ./wlr-which-key.nix
    ./mako.nix
    ../quickshell/window-switcher/quickshell-window-switcher-home-manager.nix
    ../quickshell/overview/quickshell-overview-home-manager.nix
    ../../../home/linux/desktop/satty.nix
    ../../../home/linux/audio/wiremix.nix
    ./xdg-desktop-portal-hyprland-service.nix
    ./focus-daemon-service.nix
    ../../../home/linux/desktop/fuzzel.nix
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
