{
  config,
  ...
}:
let
  workspacePath = config.openclaw.workspacePath;
  workspaceInstructionsPath = ../../../agents/openclaw/workspace;

  filenames = (builtins.attrNames (builtins.readDir workspaceInstructionsPath));

  files = builtins.listToAttrs (
    map (filename: {
      name = "${workspacePath}/${filename}";
      value.text = builtins.readFile (workspaceInstructionsPath + "/${filename}");
    }) filenames
  );
in
{
  home.file = files;
}
