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
    tmuxSessionName
    clawdeRuntimePaths
    clawdeServiceSpecificationFile
    ;

  clawdeServiceScript = ./scripts/clawde-service.py;

  clawdeSessionStarter = pkgs.writeShellScriptBin "clawde" ''
    export TMUX_BIN=${pkgs.tmux}/bin/tmux
    export TMUX_SESSION_NAME=${lib.escapeShellArg tmuxSessionName}
    export SYSTEMD_USER_SERVICE_NAME=clawde
    export LAUNCHD_LABEL=org.nix-community.home.clawde
    ${builtins.readFile ./scripts/start-clawde.sh}
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
    home.packages = [ clawdeSessionStarter ];

    systemd.user.services = lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
      clawde = linuxSystemdUnit;
    };

    launchd.agents = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
      clawde = darwinLaunchdAgent;
    };
  };
}
