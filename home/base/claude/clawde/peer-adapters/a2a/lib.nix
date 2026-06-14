{
  pkgs,
  lib,
}:
let
  a2aPeerAdapterInstructions = builtins.readFile ./instructions/a2a-peer-runtime.md;

  repoAgentsDirectory = ./.;

  resolveA2APeerPublicEndpointUrl =
    agent:
    if agent.expose.a2a.publicEndpointUrl != null then
      agent.expose.a2a.publicEndpointUrl
    else
      "http://${agent.expose.a2a.listenHost}:${toString agent.expose.a2a.listenPort}";

  resolveA2APeerCardDescription =
    name: agent:
    if agent.expose.a2a.agentDescriptionForCard != "" then
      agent.expose.a2a.agentDescriptionForCard
    else
      "clawde agent ${name}";

  buildA2APeerWindowCommand =
    name: agent:
    pkgs.writeShellScript "clawde-a2a-peer-${name}" (
      lib.concatStringsSep " " [
        "exec"
        "env"
        "PYTHONPATH=${repoAgentsDirectory}"
        "${pkgs.python312}/bin/python3"
        "-m"
        "a2a_server"
        "--agent-name"
        (lib.escapeShellArg name)
        "--agent-description"
        (lib.escapeShellArg (resolveA2APeerCardDescription name agent))
        "--listen-host"
        (lib.escapeShellArg agent.expose.a2a.listenHost)
        "--listen-port"
        (toString agent.expose.a2a.listenPort)
        "--public-endpoint-url"
        (lib.escapeShellArg (resolveA2APeerPublicEndpointUrl agent))
        "--backend-type"
        "tmux"
        "--tmux-meaningful-line-pattern"
        (lib.escapeShellArg agent.expose.a2a.tmuxMeaningfulLinePattern)
        "--tmux-session-name"
        (lib.escapeShellArg agent.tmuxSession)
        "--tmux-window-name"
        (lib.escapeShellArg name)
      ]
    );

  buildA2APeerWindowSpecification = name: agent: {
    name = "${name}-a2a";
    wrapper_command = "${buildA2APeerWindowCommand name agent}";
  };
in
{
  instructionsBlockForAgent =
    agent: if agent.expose.a2a.enable then a2aPeerAdapterInstructions else "";

  peerWindowSpecificationsForAgent =
    name: agent: lib.optional agent.expose.a2a.enable (buildA2APeerWindowSpecification name agent);
}
