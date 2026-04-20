{
  systemd.user.services.github-actions-runner = {
    Unit = {
      Description = "GitHub Actions self-hosted runner for private-gitlab-heatmap-exporter";
      After = [ "network-online.target" ];
    };

    Service = {
      WorkingDirectory = "%h/actions-runner";
      ExecStart = "%h/actions-runner/run.sh";
      KillSignal = "SIGTERM";
      TimeoutStopSec = "5min";
      RuntimeMaxSec = "60min";
    };
  };

  systemd.user.timers.github-actions-runner = {
    Unit = {
      Description = "Start GitHub Actions runner before scheduled workflow (12:00 BRT)";
    };

    Timer = {
      OnCalendar = "11:30";
      Persistent = true;
    };

    Install = {
      WantedBy = [ "timers.target" ];
    };
  };
}
