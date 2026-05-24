{
  config,
  lib,
  ...
}:
let
  cfg = config.clawde;
  agentsExposingA2A = lib.filterAttrs (_: agent: agent.expose.a2a.enable) cfg.agents;
  hasA2AAgents = agentsExposingA2A != { };

  agentNamesByListenPort = lib.foldlAttrs (
    accumulator: name: agent:
    accumulator
    // {
      ${toString agent.expose.a2a.listenPort} =
        (accumulator.${toString agent.expose.a2a.listenPort} or [ ])
        ++ [
          name
        ];
    }
  ) { } agentsExposingA2A;

  listenPortsWithMultipleClaimingAgents = lib.filterAttrs (
    _: agentNames: builtins.length agentNames > 1
  ) agentNamesByListenPort;
in
{
  config = lib.mkIf hasA2AAgents {
    assertions =
      (lib.mapAttrsToList (name: agent: {
        assertion = agent.expose.a2a.listenPort > 0 && agent.expose.a2a.listenPort < 65536;
        message = "Agent ${name}: expose.a2a.listenPort must be a valid TCP port (1-65535)";
      }) agentsExposingA2A)
      ++ (lib.mapAttrsToList (listenPort: claimingAgentNames: {
        assertion = false;
        message = "expose.a2a.listenPort ${listenPort} is claimed by multiple clawde agents: ${lib.concatStringsSep ", " claimingAgentNames}. Pick distinct ports per agent.";
      }) listenPortsWithMultipleClaimingAgents);
  };
}
