{ lib, pkgs, ... }:
let
  systemctl = "${pkgs.systemd}/bin/systemctl";
  timeout = "${pkgs.coreutils}/bin/timeout";
  graphicalServiceRestartTimeoutSeconds = 60;
  graphicalServices = [
    "mako.service"
    "xdg-desktop-portal-hyprland.service"
    "hypr-focus-daemon.service"
    "clipse.service"
  ];
in
{
  home.activation.startGraphicalServices = lib.hm.dag.entryAfter [ "reloadSystemd" ] ''
    HYPR_DIR="/run/user/$(id -u)/hypr"
    if [ -d "$HYPR_DIR" ] && [ "$(ls -A "$HYPR_DIR" 2>/dev/null)" ]; then
      $DRY_RUN_CMD ${timeout} ${toString graphicalServiceRestartTimeoutSeconds} ${systemctl} --user restart ${lib.concatStringsSep " " graphicalServices} || true
    fi
  '';
}
