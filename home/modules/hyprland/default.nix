# Shared Hyprland modules - does NOT include Hyprland binary
# Import via nixos.nix or standalone.nix instead
{ lib, pkgs, ... }:
let
  systemctl = "${pkgs.systemd}/bin/systemctl";
  graphicalServices = [
    "waybar.service"
    "swaync.service"
    "hyprshell.service"
    "swayosd.service"

  ];
in
{
  imports = [
    ./packages.nix
    ./calendar.nix
    ./cursor.nix
    ./omarchy.nix
    ./waybar.nix
    ./hyprshell.nix
    ./wlogout.nix
    ./swayosd.nix
    ./wayland-electron.nix
    ./waybar-service.nix

    ./swaync-service.nix
    ../fuzzel.nix
  ];

  # Start graphical services after systemd reload
  # This ensures services restart after home-manager switch
  home.activation.startGraphicalServices = lib.hm.dag.entryAfter [ "reloadSystemd" ] ''
    HYPR_DIR="/run/user/$(id -u)/hypr"
    if [ -d "$HYPR_DIR" ] && [ "$(ls -A "$HYPR_DIR" 2>/dev/null)" ]; then
      $DRY_RUN_CMD ${systemctl} --user start ${lib.concatStringsSep " " graphicalServices} || true
    fi
  '';
}
