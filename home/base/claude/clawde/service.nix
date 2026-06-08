{
  config,
  lib,
  pkgs,
  ...
}:
let
  helpers = import ./lib.nix { inherit pkgs config lib; };
  inherit (helpers)
    hasAgents
    homeDir
    defaultTmuxSessionName
    clawdeRuntimePaths
    clawdeServiceSpecificationFile
    ;

  clawdeServiceScript = ./scripts/clawde-service.py;

  clawdeSessionStarter = pkgs.writeShellScriptBin "clawde" ''
    export TMUX_BIN=${pkgs.tmux}/bin/tmux
    export DEFAULT_TMUX_SESSION_NAME=${lib.escapeShellArg defaultTmuxSessionName}
    export SYSTEMD_USER_SERVICE_NAME=clawde
    export LAUNCHD_LABEL=org.nix-community.home.clawde
    ${builtins.readFile ./scripts/start-clawde.sh}
  '';

  clawdeGracefulRedeployScript = ./scripts/clawde-redeploy.py;
  clawdeResumeNudgeScript = "${./scripts/heartbeat}/resume_nudge.py";

  clawdeGracefulRedeploy = pkgs.writeShellScriptBin "clawde-redeploy" ''
    export CLAWDE_RESUME_NUDGE_SCRIPT=${clawdeResumeNudgeScript}
    exec ${pkgs.python312}/bin/python3 ${clawdeGracefulRedeployScript} "$@"
  '';

  clawdeServiceExecArguments = [
    "${pkgs.python312}/bin/python3"
    "${clawdeServiceScript}"
    "--specification-file"
    "${clawdeServiceSpecificationFile}"
  ];

  linuxSystemdUnit = {
    Unit = {
      Description = "clawde persistent agents supervisor";
      After = [
        "network.target"
        "agenix.service"
      ];
      Wants = [ "agenix.service" ];
      StartLimitBurst = 5;
      StartLimitIntervalSec = 300;
      X-RestartIfChanged = false;
    };
    Service = {
      Type = "simple";
      ExecStart = lib.concatStringsSep " " clawdeServiceExecArguments;
      Restart = "always";
      RestartSec = "10s";
      KillMode = "process";
      Environment = [
        "PATH=${clawdeRuntimePaths}"
        "HOME=${homeDir}"
        "TMUX_TMPDIR=%t"
        "XDG_RUNTIME_DIR=%t"
      ];
    };
    Install = {
      WantedBy = [ "default.target" ];
    };
  };

  # launchd has no After/Wants equivalent for ordering against agenix's
  # decrypt step. ThrottleInterval=10 plus the python service script's own
  # retry on missing secret files is the workaround: clawde restarts itself
  # until ~/.secrets/<token> appears. Acceptable as long as agents on this
  # host only need secrets that are nice-to-have at start time.
  darwinLaunchdAgent = {
    enable = true;
    config = {
      ProgramArguments = clawdeServiceExecArguments;
      KeepAlive = true;
      RunAtLoad = true;
      ThrottleInterval = 10;
      EnvironmentVariables = {
        PATH = clawdeRuntimePaths;
        HOME = homeDir;
      };
      StandardOutPath = "${homeDir}/Library/Logs/clawde.out.log";
      StandardErrorPath = "${homeDir}/Library/Logs/clawde.err.log";
    };
  };
in
{
  config = lib.mkIf hasAgents {
    home.packages = [
      clawdeSessionStarter
      clawdeGracefulRedeploy
    ];

    systemd.user.services = lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
      clawde = linuxSystemdUnit;
    };

    launchd.agents = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
      clawde = darwinLaunchdAgent;
    };
  };
}
