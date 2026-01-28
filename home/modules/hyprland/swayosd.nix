{ pkgs, ... }:
let
  swayosdStart = pkgs.writeShellScript "swayosd-start" ''
    # Wait for Hyprland to be ready (avoids race condition panic)
    for i in $(seq 1 30); do
      if hyprctl monitors &>/dev/null; then
        break
      fi
      sleep 0.2
    done
    exec ${pkgs.swayosd}/bin/swayosd-server -s ${pkgs.swayosd}/etc/xdg/swayosd/style.css
  '';
in
{
  systemd.user.services.swayosd = {
    Unit = {
      Description = "SwayOSD notification daemon";
      Documentation = "https://github.com/ErikReider/SwayOSD";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "simple";
      ExecStart = "${swayosdStart}";
      Restart = "always";
      RestartSec = "2s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
