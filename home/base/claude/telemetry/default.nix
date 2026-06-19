{
  pkgs,
  lib,
  config,
  ...
}:
let
  collectorPackage = pkgs.opentelemetry-collector-contrib;
  metricsDirectory = "${config.home.homeDirectory}/.claude/otel-metrics";
  metricsFilePath = "${metricsDirectory}/metrics.jsonl";

  collectorConfigFile = pkgs.writeText "claude-otel-collector-config.yaml" ''
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 127.0.0.1:4317
          http:
            endpoint: 127.0.0.1:4318
    processors:
      batch: {}
    exporters:
      file:
        path: ${metricsFilePath}
        rotation:
          max_megabytes: 5
          max_backups: 3
          max_days: 14
    service:
      telemetry:
        logs:
          level: warn
      pipelines:
        metrics:
          receivers: [otlp]
          processors: [batch]
          exporters: [file]
  '';

  collectorProgramArguments = [
    "${collectorPackage}/bin/otelcol-contrib"
    "--config"
    "${collectorConfigFile}"
  ];

  ensureMetricsDirectory = pkgs.writeShellScript "claude-otel-ensure-metrics-directory" ''
    mkdir -p ${lib.escapeShellArg metricsDirectory}
  '';
in
{
  imports = [
    ./usage-snapshot-upload.nix
  ];

  config = lib.mkMerge [
    {
      home.activation.ensureClaudeOtelMetricsDirectory = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${ensureMetricsDirectory}
      '';
    }
    (lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
      launchd.agents.claude-otel-collector = {
        enable = true;
        config = {
          Label = "com.dotfiles.claude-otel-collector";
          ProgramArguments = collectorProgramArguments;
          RunAtLoad = true;
          KeepAlive = true;
          StandardOutPath = "/tmp/claude-otel-collector.log";
          StandardErrorPath = "/tmp/claude-otel-collector.log";
        };
      };
    })
    (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
      systemd.user.services.claude-otel-collector = {
        Unit = {
          Description = "Local OpenTelemetry collector for Claude Code metrics";
          After = [ "default.target" ];
        };
        Service = {
          ExecStart = lib.concatStringsSep " " collectorProgramArguments;
          Restart = "always";
          RestartSec = 5;
        };
        Install.WantedBy = [ "default.target" ];
      };
    })
  ];
}
