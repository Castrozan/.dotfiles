{
  lib,
  config,
  ...
}:
let
  inherit (config) openclaw;
  rulesSourcePath = ../../../agents/rules;

  filenames = builtins.attrNames (builtins.readDir rulesSourcePath);

  # Generate rules files for a specific agent
  mkAgentFiles =
    agentName:
    builtins.listToAttrs (
      map (filename: {
        name = "rules/${filename}";
        value.text = openclaw.substituteAgentConfig agentName (rulesSourcePath + "/${filename}");
      }) filenames
    );

  # Deploy to all enabled agents
  allFiles = lib.foldl' (
    acc: agentName: acc // (openclaw.deployToWorkspace agentName (mkAgentFiles agentName))
  ) { } (lib.attrNames openclaw.enabledAgents);
in
{
  home.file = allFiles;
}
