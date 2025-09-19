{ pkgs, ... }:
{
  home.packages = [ pkgs.clipse ];

  systemd.user.services.clipse = {
    Unit = {
      Description = "Clipse clipboard manager daemon";
      After = [ "graphical-session.target" ];
    };
    Service = {
      Type = "simple";
      ExecStart = "${pkgs.clipse}/bin/clipse --listen";
      Restart = "always";
      RestartSec = 3;
    };
    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
