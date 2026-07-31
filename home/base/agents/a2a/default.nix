{
  pkgs,
  config,
  lib,
  ...
}:
let
  declaredClawdeAgents = lib.attrByPath [ "clawde" "agents" ] { } config;

  agentsExposedAsA2APeers = lib.filterAttrs (_: agent: agent.expose.a2a.enable) declaredClawdeAgents;

  peerEndpointUrl =
    agent:
    if agent.expose.a2a.publicEndpointUrl != null then
      agent.expose.a2a.publicEndpointUrl
    else
      "http://${agent.expose.a2a.listenHost}:${toString agent.expose.a2a.listenPort}";

  peerRegistry = {
    peers = lib.mapAttrs (name: agent: {
      endpoint = peerEndpointUrl agent;
      description =
        if agent.expose.a2a.agentDescriptionForCard != "" then
          agent.expose.a2a.agentDescriptionForCard
        else
          "clawde agent ${name}";
    }) agentsExposedAsA2APeers;
  };

  a2aCommandLineInterface = pkgs.writeShellScriptBin "a2a" ''
    export PYTHONPATH=${./scripts}
    exec ${pkgs.python312}/bin/python3 -m a2a_cli "$@"
  '';
in
{
  home.packages = [ a2aCommandLineInterface ];

  home.file.".claude/a2a/peers.json".text = builtins.toJSON peerRegistry;
}
