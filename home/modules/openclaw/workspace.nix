{
  config,
  ...
}:
let
  openclaw = config.openclaw;
  workspaceSourcePath = ../../../agents/openclaw/workspace;

  filenames = builtins.attrNames (builtins.readDir workspaceSourcePath);

  files = builtins.listToAttrs (
    map (filename: {
      name = filename;
      value.text = openclaw.substituteAgentConfig (workspaceSourcePath + "/${filename}");
    }) filenames
  );
in
{
  home.file = openclaw.deployToBoth files;
}
