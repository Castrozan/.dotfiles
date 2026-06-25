{
  pkgs,
  lib,
  ...
}:
let
  watchdogInvocationIntervalSeconds = 15;

  watchdogPythonEnvironment = pkgs.python312.withPackages (pythonPackages: [
    pythonPackages.psutil
  ]);

  watchdogScriptSource = lib.fileset.toSource {
    root = ../../../../agents/skills/browser/install/watchdog;
    fileset = ../../../../agents/skills/browser/install/watchdog/kill_runaway_chrome_devtools_mcp_instances.py;
  };

  watchdogProgramArguments = [
    "${watchdogPythonEnvironment}/bin/python"
    "${watchdogScriptSource}/kill_runaway_chrome_devtools_mcp_instances.py"
  ];

  watchdogLogFilePath = "/tmp/chrome-devtools-mcp-runaway-watchdog.log";
in
{
  config = lib.mkMerge [
    (lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
      launchd.agents.chrome-devtools-mcp-runaway-watchdog = {
        enable = true;
        config = {
          Label = "com.dotfiles.chrome-devtools-mcp-runaway-watchdog";
          ProgramArguments = watchdogProgramArguments;
          RunAtLoad = true;
          StartInterval = watchdogInvocationIntervalSeconds;
          StandardOutPath = watchdogLogFilePath;
          StandardErrorPath = watchdogLogFilePath;
        };
      };
    })
    (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
      systemd.user.services.chrome-devtools-mcp-runaway-watchdog = {
        Unit.Description = "Terminate runaway chrome-devtools-mcp instances pinning CPU";
        Service = {
          Type = "oneshot";
          ExecStart = lib.concatStringsSep " " watchdogProgramArguments;
        };
      };
      systemd.user.timers.chrome-devtools-mcp-runaway-watchdog = {
        Unit.Description = "Periodic runaway chrome-devtools-mcp watchdog";
        Timer = {
          OnBootSec = "1min";
          OnUnitActiveSec = "${toString watchdogInvocationIntervalSeconds}s";
          Persistent = true;
        };
        Install.WantedBy = [ "timers.target" ];
      };
    })
  ];
}
