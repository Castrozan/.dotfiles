{
  config,
  ...
}:
let
  openclaw = config.openclaw;
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

  files = builtins.listToAttrs (
    map (filename: {
      name = filename;
      value.text = openclaw.substituteAgentConfig (workspaceSourcePath + "/${filename}");
    }) filenames
  );
in
{
  home.file = openclaw.deployToWorkspace files;
}
