{
  systemd.user.services.github-actions-runner = {
    Unit = {
      Description = "GitHub Actions self-hosted runner for private-gitlab-heatmap-exporter";
      After = [ "network-online.target" ];
    };

    Service = {
      WorkingDirectory = "%h/actions-runner";
      ExecStart = "%h/actions-runner/run.sh";
      KillMode = "process";
      KillSignal = "SIGTERM";
      TimeoutStopSec = "5min";
      RuntimeMaxSec = "45min";
    };
  };

  systemd.user.timers.github-actions-runner = {
    Unit = {
      Description = "Start GitHub Actions runner before scheduled workflow (11:45 BRT)";
    };

    Timer = {
      OnCalendar = "11:45";
      Persistent = true;
    };

    Install = {
      WantedBy = [ "timers.target" ];
    };
  };
}
