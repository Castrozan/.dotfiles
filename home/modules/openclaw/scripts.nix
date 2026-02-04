{
  lib,
  config,
  ...
}:
let
  inherit (config) openclaw;
  scriptsSourcePath = ../../../agents/scripts;

  filenames = builtins.filter (name: lib.hasSuffix ".sh" name || lib.hasSuffix ".py" name) (
    builtins.attrNames (builtins.readDir scriptsSourcePath)
  );

  # Generate scripts files for a specific agent
  mkAgentFiles =
    agentName:
    builtins.listToAttrs (
      map (filename: {
        name = "scripts/${filename}";
        value = {
          text = openclaw.substituteAgentConfig agentName (scriptsSourcePath + "/${filename}");
          executable = true;
        };
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
