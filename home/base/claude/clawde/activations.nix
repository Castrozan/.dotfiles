{
  config,
  lib,
  pkgs,
  ...
}:
let
  helpers = import ./lib.nix { inherit pkgs config lib; };
  inherit (helpers)
    cfg
    hasAgents
    agentNames
    agentWorkspaceDirectory
    claudeBinary
    ;

  getChannelAdapterFor = agent: cfg.channelAdapters.${agent.channel.type} or null;

  perAgentChannelAdapterActivationLines = lib.concatMapStringsSep "\n" (
    name:
    let
      agent = cfg.agents.${name};
      adapter = getChannelAdapterFor agent;
      workspaceDirectory = agentWorkspaceDirectory name;
    in
    if adapter != null then
      adapter.agentActivationScriptFor {
        inherit
          name
          agent
          workspaceDirectory
          claudeBinary
          ;
      }
    else
      ""
  ) agentNames;

  runAllChannelAdapterAgentActivations = pkgs.writeShellScript "clawde-run-all-channel-adapter-agent-activations" perAgentChannelAdapterActivationLines;

  seedOneMemoryBridgeScript = pkgs.writeShellScript "seed-one-memory-bridge" (
    builtins.readFile ./scripts/seed-memory-bridge.sh
  );

  seedAllMemoryBridges = pkgs.writeShellScript "seed-all-memory-bridges" (
    lib.concatMapStringsSep "\n" (
      name: "${seedOneMemoryBridgeScript} ${lib.escapeShellArg (agentWorkspaceDirectory name)}"
    ) agentNames
  );

  channelAdapterPreActivationLines = lib.concatMapStringsSep "\n" (
    adapterName:
    let
      adapter = cfg.channelAdapters.${adapterName};
    in
    if adapter.preActivation != null then adapter.preActivation else ""
  ) (builtins.attrNames cfg.channelAdapters);
in
{
  config = lib.mkIf hasAgents {
    home.activation = {
      runChannelAdapterPreActivations = lib.hm.dag.entryAfter [
        "writeBoundary"
      ] channelAdapterPreActivationLines;

      runChannelAdapterAgentActivations = lib.hm.dag.entryAfter [ "runChannelAdapterPreActivations" ] ''
        run ${runAllChannelAdapterAgentActivations}
      '';

      seedAgentMemoryBridges = lib.hm.dag.entryAfter [ "runChannelAdapterAgentActivations" ] ''
        run ${seedAllMemoryBridges}
      '';
    };
  };
}
