{
  config,
  lib,
  pkgs,
  healthCheckLib,
  ...
}:
let
  agentWrapperDirectory = ./scripts/agent-wrapper;
  agentPaneStuckModalCheckerScript = "${agentWrapperDirectory}/check_agent_pane_for_stuck_modal.py";

  clawdeAgentProcessProbes = lib.mapAttrsToList (
    agentName: _agentConfig:
    healthCheckLib.mkProcessProbe {
      name = "clawde agent: ${agentName}";
      pattern = "agent-wrapper/wrapper.py --agent-name ${agentName}";
    }
  ) config.clawde.agents;

  clawdeAgentPaneLivenessProbes = lib.mapAttrsToList (
    agentName: agentConfig:
    healthCheckLib.mkCommandProbe {
      name = "clawde agent pane liveness: ${agentName}";
      command = lib.concatStringsSep " " [
        "PYTHONPATH=${lib.escapeShellArg agentWrapperDirectory}"
        "${pkgs.python312}/bin/python3"
        "${agentPaneStuckModalCheckerScript}"
        "--tmux-target"
        (lib.escapeShellArg "${agentConfig.tmuxSession}:${agentName}")
      ];
    }
  ) config.clawde.agents;

  clawdeAgentProbes = clawdeAgentProcessProbes ++ clawdeAgentPaneLivenessProbes;

  clawdeServiceProbe =
    if pkgs.stdenv.hostPlatform.isDarwin then
      healthCheckLib.mkLaunchdProbe {
        name = "clawde service (launchd)";
        label = "org.nix-community.home.clawde";
      }
    else
      healthCheckLib.mkSystemdUserUnitProbe {
        name = "clawde service (systemd)";
        unit = "clawde.service";
      };

  clawdeServiceEnabled = (lib.length clawdeAgentProbes) > 0;
in
{
  healthCheck.probes = clawdeAgentProbes ++ lib.optional clawdeServiceEnabled clawdeServiceProbe;
}
