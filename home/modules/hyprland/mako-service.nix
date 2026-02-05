{ pkgs, ... }:
let
  makoStart = pkgs.writeShellScript "mako-start" ''
    THEME_CONFIG="$HOME/.config/omarchy/current/theme/mako.conf"
    if [[ -f "$THEME_CONFIG" ]]; then
      exec ${pkgs.mako}/bin/mako -c "$THEME_CONFIG"
    else
      exec ${pkgs.mako}/bin/mako
    fi
  '';
in
{
  home.packages = [ pkgs.mako ];

  systemd.user.services.mako = {
    Unit = {
      Description = "Mako notification daemon";
      Documentation = "https://github.com/emersion/mako";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "simple";
      ExecStart = "${makoStart}";
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
