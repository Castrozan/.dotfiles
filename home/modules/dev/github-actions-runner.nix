{
  systemd.user.services.github-actions-runner = {
    Unit = {
      Description = "GitHub Actions self-hosted runner for private-gitlab-heatmap-exporter";
      After = [ "network-online.target" ];
      Wants = [ "network-online.target" ];
    };

    Service = {
      WorkingDirectory = "%h/actions-runner";
      ExecStart = "%h/actions-runner/run.sh";
      KillMode = "process";
      KillSignal = "SIGTERM";
      TimeoutStopSec = "5min";
      Restart = "on-failure";
      RestartSec = 10;
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };
}
