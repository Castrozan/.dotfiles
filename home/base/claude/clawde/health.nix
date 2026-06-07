{
  config,
  lib,
  pkgs,
  healthCheckLib,
  ...
}:
let
  clawdeAgentProbes = lib.mapAttrsToList (
    agentName: _agentConfig:
    healthCheckLib.mkProcessProbe {
      name = "clawde agent: ${agentName}";
      pattern = "agent-wrapper/wrapper.py --agent-name ${agentName}";
    }
  ) config.clawde.agents;

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
