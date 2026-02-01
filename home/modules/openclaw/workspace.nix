{
  config,
  ...
}:
let
  openclaw = config.openclaw;
  workspaceSourcePath = ../../../agents/openclaw/workspace;

  filenames = builtins.attrNames (builtins.readDir workspaceSourcePath);

  workspaceFiles = builtins.listToAttrs (
    map (filename: {
      name = "${openclaw.workspacePath}/${filename}";
      value.text = openclaw.substituteAgentConfig (workspaceSourcePath + "/${filename}");
    }) filenames
  );
in
{
  home.file = workspaceFiles;
}
