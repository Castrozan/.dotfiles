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

  activeHoursFlags =
    agent:
    if agent.activeHoursStart != null then
      "--active-hours-start ${toString agent.activeHoursStart} --active-hours-end ${toString agent.activeHoursEnd}"
    else
      "";

  buildServiceScript =
    name: agent:
    pkgs.writeShellScript "claude-project-agent-${name}" ''
      set -Eeuo pipefail
      export PROJECT_AGENT_INSTRUCTIONS="${instructionsFile}"
      ${lib.optionalString (
        agent.extraInstructionsFile != null
      ) ''export PROJECT_AGENT_EXTRA_INSTRUCTIONS="${agent.extraInstructionsFile}"''}
      export CLAUDE_BINARY_PATH="${config.claude.package}/bin/claude"
      exec ${pkgs.python312}/bin/python3 ${./scripts/launch-project-agent} \
        ${lib.escapeShellArg agent.projectDirectory} \
        --name ${lib.escapeShellArg name} \
        --model ${lib.escapeShellArg agent.model} \
        --heartbeat ${lib.escapeShellArg agent.heartbeatInterval} \
        --keepalive \
        ${activeHoursFlags agent}
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
          activeHoursStart = lib.mkOption {
            type = lib.types.nullOr lib.types.int;
            default = null;
            description = "Hour (0-23) when agent should start running. Must be set together with activeHoursEnd.";
          };
          activeHoursEnd = lib.mkOption {
            type = lib.types.nullOr lib.types.int;
            default = null;
            description = "Hour (0-23) when agent should stop running. Must be set together with activeHoursStart.";
          };
          extraInstructionsFile = lib.mkOption {
            type = lib.types.nullOr lib.types.path;
            default = null;
            description = "Path to project-specific instructions file appended after the base PM instructions";
          };
        };
      }
    );
    default = { };
    description = "Project manager agents - each becomes a persistent Claude Code session with heartbeat loop";
  };

  config = lib.mkIf hasAgents {
    assertions = map (
      name:
      let
        agent = cfg.agents.${name};
      in
      {
        assertion = (agent.activeHoursStart == null) == (agent.activeHoursEnd == null);
        message = "Project agent ${name}: activeHoursStart and activeHoursEnd must both be set or both be null";
      }
    ) agentNames;

    systemd.user.services = lib.mapAttrs' (name: agent: {
      name = "claude-project-agent-${name}";
      value = {
        Unit = {
          Description = "Claude Code project agent: ${name}";
          After = [ "network.target" ];
          StartLimitBurst = 5;
          StartLimitIntervalSec = 300;
        };
        Service = {
          Type = "simple";
          ExecStart = "${buildServiceScript name agent}";
          Restart = if agent.activeHoursStart != null then "always" else "on-failure";
          RestartSec = "10s";
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
