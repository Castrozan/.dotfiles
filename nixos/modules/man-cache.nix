{ pkgs, ... }:
{
  documentation.man.generateCaches = false;

  systemd.services.update-man-db = {
    description = "Update man-db cache";
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${pkgs.man-db}/bin/mandb";
    };
  };

  systemd.timers.update-man-db = {
    description = "Timer for updating man-db cache";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "daily";
      Persistent = true;
    };
  };
}
