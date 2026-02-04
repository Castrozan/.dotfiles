{
  lib,
  config,
  ...
}:
let
  inherit (config) openclaw;

  # Generate tts.json for each enabled agent
  allFiles = lib.foldl' (
    acc: agentName:
    let
      agent = openclaw.agents.${agentName};
    in
    acc
    // (openclaw.deployToWorkspace agentName {
      "tts.json".text = builtins.toJSON {
        inherit (agent.tts) engine;
        inherit (agent.tts) voice;
      };
    })
  ) { } (lib.attrNames openclaw.enabledAgents);
in
{
  home.file = allFiles;
}
