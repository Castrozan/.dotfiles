{ pkgs, ... }:
let
  makoStart = pkgs.writeShellScript "mako-start" ''
    THEME_CONFIG="$HOME/.config/hypr-theme/current/theme/mako.conf"
    if [[ -f "$THEME_CONFIG" ]]; then
      exec ${pkgs.mako}/bin/mako -c "$THEME_CONFIG"
    else
      exec ${pkgs.mako}/bin/mako
    fi
  '';

  makoctl-without-dbus-activation = pkgs.runCommand "makoctl-without-dbus-activation" { } ''
    mkdir -p $out/bin
    ln -s ${pkgs.mako}/bin/makoctl $out/bin/makoctl
  '';
in
{
  home.packages = [ makoctl-without-dbus-activation ];

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
