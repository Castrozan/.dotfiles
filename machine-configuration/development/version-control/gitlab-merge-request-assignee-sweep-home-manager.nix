{
  config,
  lib,
  pkgs,
  ...
}:
let
  sweepName = "gitlab-merge-request-assignee-sweep";
  sweepIntervalSeconds = 60;
  launchdLogByteLimit = 1048576;

  stateDirectory = "${config.xdg.stateHome}/${sweepName}";
  launchdLogFile = "${config.home.homeDirectory}/Library/Logs/${sweepName}.log";

  hostArguments = lib.concatMapStringsSep " " (
    host: "--host ${lib.escapeShellArg host}"
  ) config.glab.authenticatedHosts;

  sweepPackage = pkgs.writeShellScriptBin sweepName ''
    export PATH="${lib.makeBinPath [ pkgs.glab ]}:$PATH"
    exec ${pkgs.python312}/bin/python3 ${./scripts/gitlab_merge_request_assignee_sweep.py} \
      ${hostArguments} \
      --state-directory ${lib.escapeShellArg stateDirectory} \
      "$@"
  '';
  sweepCommand = "${sweepPackage}/bin/${sweepName}";

  launchdSweepWithBoundedLog = pkgs.writeShellScript "${sweepName}-with-bounded-log" ''
    log_file=${lib.escapeShellArg launchdLogFile}
    if [ -f "$log_file" ] && [ "$(${pkgs.coreutils}/bin/wc -c < "$log_file")" -gt ${toString launchdLogByteLimit} ]; then
      : > "$log_file"
    fi
    exec ${sweepCommand}
  '';
in
{
  config = lib.mkIf (config.glab.authenticatedHosts != [ ]) (
    lib.mkMerge [
      { home.packages = [ sweepPackage ]; }

      (lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
        launchd.agents.${sweepName} = {
          enable = true;
          config = {
            Label = "com.dotfiles.${sweepName}";
            ProgramArguments = [ "${launchdSweepWithBoundedLog}" ];
            RunAtLoad = true;
            StartInterval = sweepIntervalSeconds;
            StandardOutPath = launchdLogFile;
            StandardErrorPath = launchdLogFile;
          };
        };
      })

      (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
        systemd.user.services.${sweepName} = {
          Unit.Description = "Assign recently opened, unassigned GitLab merge requests to their author";
          Service = {
            Type = "oneshot";
            ExecStart = sweepCommand;
          };
        };
        systemd.user.timers.${sweepName} = {
          Unit.Description = "Run the GitLab merge request assignee sweep every minute";
          Timer = {
            OnCalendar = "minutely";
            AccuracySec = "5s";
          };
          Install.WantedBy = [ "timers.target" ];
        };
      })
    ]
  );
}
