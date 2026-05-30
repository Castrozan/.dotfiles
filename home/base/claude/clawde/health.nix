{
  config,
  lib,
  healthCheckLib,
  ...
}:
{
  healthCheck.probes = lib.mapAttrsToList (
    agentName: _agentConfig:
    healthCheckLib.mkProcessProbe {
      name = "clawde agent: ${agentName}";
      pattern = "clawde-agent-wrapper.py --agent-name ${agentName}";
    }
  ) config.clawde.agents;
}
