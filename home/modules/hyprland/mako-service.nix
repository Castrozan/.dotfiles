{ pkgs, ... }:
let
  makoStart = pkgs.writeShellScript "mako-start" ''
    BASE_CONFIG="$HOME/.config/mako/config"
    THEME_COLORS="$HOME/.config/omarchy/current/theme/mako.ini"
    MERGED_CONFIG="$HOME/.cache/omarchy/mako-merged.ini"

    mkdir -p "$(dirname "$MERGED_CONFIG")"

    if [[ -f "$THEME_COLORS" ]]; then
      { cat "$BASE_CONFIG"; echo ""; cat "$THEME_COLORS"; } > "$MERGED_CONFIG"
      exec ${pkgs.mako}/bin/mako -c "$MERGED_CONFIG"
    else
      exec ${pkgs.mako}/bin/mako -c "$BASE_CONFIG"
    fi
  '';
in
{
  systemd.user.services.mako = {
    Unit = {
      Description = "Mako notification daemon";
      Documentation = "https://github.com/emersion/mako";
      PartOf = [ "graphical-session.target" ];
      After = [ "graphical-session.target" ];
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
