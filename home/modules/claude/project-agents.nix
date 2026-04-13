{
  pkgs,
  config,
  lib,
  ...
}:
let
  cfg = config.claude.projectAgents;
  homeDir = config.home.homeDirectory;
  inherit (config.home) username;
  instructionsFile = ./project-agent/instructions.md;
  hasAgents = cfg.agents != { };
  agentNames = builtins.attrNames cfg.agents;

  nixSystemPaths = lib.concatStringsSep ":" [
    "${pkgs.tmux}/bin"
    "${pkgs.python312}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${username}/bin"
    "${homeDir}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

  buildServiceScript =
    name: agent:
    pkgs.writeShellScript "claude-project-agent-${name}" ''
      set -Eeuo pipefail
      export PROJECT_AGENT_INSTRUCTIONS="${instructionsFile}"
      exec ${pkgs.python312}/bin/python3 ${./scripts/launch-project-agent} \
        ${lib.escapeShellArg agent.projectDirectory} \
        --name ${lib.escapeShellArg name} \
        --model ${lib.escapeShellArg agent.model} \
        --heartbeat ${lib.escapeShellArg agent.heartbeatInterval} \
        --keepalive
    '';

  seedProjectAgentWorkspaces = pkgs.writeShellScript "seed-project-agent-workspaces" (
    lib.concatMapStringsSep "\n" (
      name:
      let
        agent = cfg.agents.${name};
      in
      ''
        mkdir -p "${agent.projectDirectory}/.pm"
        if [ ! -f "${agent.projectDirectory}/.pm/HEARTBEAT.md" ]; then
          printf '# Heartbeat\n\nNo active work.\n' > "${agent.projectDirectory}/.pm/HEARTBEAT.md"
        fi
      ''
    ) agentNames
  );
in
{
  options.claude.projectAgents.agents = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options = {
          projectDirectory = lib.mkOption {
            type = lib.types.str;
            description = "Absolute path to the project directory (must contain CLAUDE.md)";
          };
          model = lib.mkOption {
            type = lib.types.str;
            default = "opus";
            description = "Claude model alias (opus, sonnet, haiku)";
          };
          heartbeatInterval = lib.mkOption {
            type = lib.types.str;
            default = "3,33 * * * *";
            description = "Cron expression for heartbeat interval";
          };
        };
      }
    );
    default = { };
    description = "Project manager agents - each becomes a persistent Claude Code session with heartbeat loop";
  };

  config = lib.mkIf hasAgents {
    systemd.user.services = lib.mapAttrs' (name: agent: {
      name = "claude-project-agent-${name}";
      value = {
        Unit = {
          Description = "Claude Code project agent: ${name}";
          After = [ "network.target" ];
        };
        Service = {
          Type = "simple";
          ExecStart = "${buildServiceScript name agent}";
          ExecStop = "-${pkgs.tmux}/bin/tmux kill-session -t ${name}";
          Restart = "always";
          RestartSec = "10s";
          StartLimitBurst = 5;
          StartLimitIntervalSec = 300;
          Environment = [
            "PATH=${nixSystemPaths}"
            "HOME=${homeDir}"
            "TMUX_TMPDIR=%t"
            "XDG_RUNTIME_DIR=%t"
          ];
        };
        Install = {
          WantedBy = [ "default.target" ];
        };
      };
    }) cfg.agents;

    home.activation.seedProjectAgentWorkspaces = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${seedProjectAgentWorkspaces}
    '';
  };
}
