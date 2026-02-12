# Shared Hyprland modules - does NOT include Hyprland binary
# Import via nixos.nix or standalone.nix instead
{ lib, pkgs, ... }:
let
  systemctl = "${pkgs.systemd}/bin/systemctl";
  graphicalServices = [
    "waybar.service"
    "mako.service"
    "xdg-desktop-portal-hyprland.service"
    "hyprshell.service"
    "swayosd.service"

  ];
in
{
  imports = [
    ./packages.nix
    ./calendar.nix
    ./cursor.nix
    ./themes.nix
    ./waybar.nix
    ./hyprshell.nix
    ./wlogout.nix
    ./swayosd.nix
    ./wayland-electron.nix
    ./waybar-service.nix

    ./wlr-which-key.nix
    ./mako-service.nix
    ../satty.nix
    ../wiremix.nix
    ./xdg-desktop-portal-hyprland-service.nix
    ../fuzzel.nix
  ];

  xdg.configFile."hypr-host/monitors.conf".text = lib.mkDefault "";
  xdg.configFile."hypr-host/input.conf".text = lib.mkDefault "";

  home.activation.ensureMonitorOverrideFile = lib.hm.dag.entryBefore [ "writeBoundary" ] ''
    touch "$HOME/.cache/hypr-monitors-override.conf"
  '';

  # Start graphical services after systemd reload
  # This ensures services restart after home-manager switch
  home.activation.startGraphicalServices = lib.hm.dag.entryAfter [ "reloadSystemd" ] ''
    HYPR_DIR="/run/user/$(id -u)/hypr"
    if [ -d "$HYPR_DIR" ] && [ "$(ls -A "$HYPR_DIR" 2>/dev/null)" ]; then
      $DRY_RUN_CMD ${systemctl} --user start ${lib.concatStringsSep " " graphicalServices} || true
    fi
  '';
}
