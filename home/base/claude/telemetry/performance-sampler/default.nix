{
  pkgs,
  lib,
  config,
  hostname,
  ...
}:
let
  sampleIntervalSeconds = 300;

  samplerPythonInterpreter = pkgs.python312;

  samplerScriptSource = lib.fileset.toSource {
    root = ./scripts;
    fileset = lib.fileset.fileFilter (file: file.hasExt "py") ./scripts;
  };

  samplerProgramArguments = [
    "${samplerPythonInterpreter}/bin/python"
    "${samplerScriptSource}/sample_host_performance_metrics.py"
  ];

  performanceMetricsStateDirectory = "${config.home.homeDirectory}/.local/state/performance-metrics";
  samplerLogFilePath = "${performanceMetricsStateDirectory}/sampler.log";

  ensurePerformanceMetricsStateDirectory = pkgs.writeShellScript "performance-sampler-ensure-state-directory" ''
    mkdir -p ${lib.escapeShellArg performanceMetricsStateDirectory}
  '';
in
{
  config = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
    home.activation.ensurePerformanceMetricsStateDirectory =
      lib.hm.dag.entryAfter [ "writeBoundary" ]
        ''
          run ${ensurePerformanceMetricsStateDirectory}
        '';

    launchd.agents.performance-sampler = {
      enable = true;
      config = {
        Label = "com.dotfiles.performance-sampler";
        ProgramArguments = samplerProgramArguments;
        EnvironmentVariables = {
          PERFORMANCE_SAMPLER_HOST = hostname;
        };
        RunAtLoad = true;
        StartInterval = sampleIntervalSeconds;
        StandardOutPath = samplerLogFilePath;
        StandardErrorPath = samplerLogFilePath;
      };
    };
  };
}
