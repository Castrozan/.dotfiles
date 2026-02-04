{
  lib,
  config,
  ...
}:
let
  inherit (config) openclaw;
  workspaceSourcePath = ../../../agents/openclaw/workspace;

  # Private files (USER.md, IDENTITY.md, SOUL.md) live in private-config/openclaw/
  excludedFiles = [
    "USER.md"
    "IDENTITY.md"
    "SOUL.md"
  ];
  filenames = builtins.filter (name: !builtins.elem name excludedFiles) (
    builtins.attrNames (builtins.readDir workspaceSourcePath)
  );

  # Generate files for a specific agent
  mkAgentFiles =
    agentName:
    builtins.listToAttrs (
      map (filename: {
        name = filename;
        value.text = openclaw.substituteAgentConfig agentName (workspaceSourcePath + "/${filename}");
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
