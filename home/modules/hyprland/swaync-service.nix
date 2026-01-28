{ pkgs, ... }:
let
  swayncStart = pkgs.writeShellScript "swaync-start" ''
    THEME_CSS="$HOME/.config/omarchy/current/theme/swaync.css"
    if [[ -f "$THEME_CSS" ]]; then
      exec ${pkgs.swaynotificationcenter}/bin/swaync --style "$THEME_CSS"
    else
      exec ${pkgs.swaynotificationcenter}/bin/swaync
    fi
  '';
in
{
  home.packages = [ pkgs.swaynotificationcenter ];

  systemd.user.services.swaync = {
    Unit = {
      Description = "Sway Notification Center";
      Documentation = "https://github.com/ErikReider/SwayNotificationCenter";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "simple";
      ExecStart = "${swayncStart}";
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
