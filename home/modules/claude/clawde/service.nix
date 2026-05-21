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
    linuxSystemPaths
    clawdeServiceSpecificationFile
    ;

  clawdeServiceScript = ./scripts/clawde-service.py;

  clawdeSessionStarter = pkgs.writeShellScriptBin "clawde" ''
    export TMUX_BIN=${pkgs.tmux}/bin/tmux
    export TMUX_SESSION_NAME=${lib.escapeShellArg tmuxSessionName}
    export SYSTEMD_USER_SERVICE_NAME=clawde
    ${builtins.readFile ./scripts/start-clawde.sh}
  '';
in
{
  config = lib.mkIf hasAgents {
    home.packages = [ clawdeSessionStarter ];

    systemd.user.services.clawde = {
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
        ExecStart = lib.concatStringsSep " " [
          "${pkgs.python312}/bin/python3"
          "${clawdeServiceScript}"
          "--specification-file"
          "${clawdeServiceSpecificationFile}"
        ];
        Restart = "always";
        RestartSec = "10s";
        KillMode = "process";
        Environment = [
          "PATH=${linuxSystemPaths}"
          "HOME=${homeDir}"
          "TMUX_TMPDIR=%t"
          "XDG_RUNTIME_DIR=%t"
        ];
      };
      Install = {
        WantedBy = [ "default.target" ];
      };
    };
  };
}
