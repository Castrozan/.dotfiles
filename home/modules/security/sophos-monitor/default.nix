{
  pkgs,
  config,
  lib,
  ...
}:
let
  dataDirectory = "${config.home.homeDirectory}/.local/share/sophos-monitor";

  collectSophosMetricsSource = pkgs.writeText "collect-sophos-metrics-source.py" (
    builtins.readFile ./scripts/collect_sophos_metrics.py
  );

  querySophosMetricsSource = pkgs.writeText "query-sophos-metrics-source.py" (
    builtins.readFile ./scripts/query_sophos_metrics.py
  );

  collectSophosMetricsScript = pkgs.writeShellScriptBin "sophos-monitor-collect" ''
    export SOPHOS_MONITOR_DATA_DIR="${dataDirectory}"
    exec ${pkgs.python312}/bin/python3 ${collectSophosMetricsSource} "$@"
  '';

  querySophosMetricsScript = pkgs.writeShellScriptBin "sophos-monitor-query" ''
    export SOPHOS_MONITOR_DATA_DIR="${dataDirectory}"
    exec ${pkgs.python312}/bin/python3 ${querySophosMetricsSource} "$@"
  '';
in
{
  home.packages = [
    collectSophosMetricsScript
    querySophosMetricsScript
  ];

  systemd.user.services.sophos-monitor-collect = {
    Unit = {
      Description = "Collect Sophos process resource metrics into SQLite database";
    };

    Service = {
      Type = "oneshot";
      ExecStart = "${collectSophosMetricsScript}/bin/sophos-monitor-collect";
      Environment = [
        "SOPHOS_MONITOR_DATA_DIR=${dataDirectory}"
        "SOPHOS_MONITOR_RETENTION_DAYS=90"
      ];
    };
  };

  systemd.user.timers.sophos-monitor-collect = {
    Unit = {
      Description = "Sophos resource monitoring collection timer";
    };

    Timer = {
      OnBootSec = "2min";
      OnUnitActiveSec = "5min";
      Persistent = true;
    };

    Install = {
      WantedBy = [ "timers.target" ];
    };
  };
}
