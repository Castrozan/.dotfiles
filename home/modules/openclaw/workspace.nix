{
  config,
  ...
}:
let
  cfg = config.openclaw;
  workspacePath = cfg.workspacePath;
  workspaceInstructionsPath = ../../../agents/openclaw/workspace;
  subs = cfg.substitutions;

  filenames = (builtins.attrNames (builtins.readDir workspaceInstructionsPath));

  files = builtins.listToAttrs (
    map (filename: {
      name = "${workspacePath}/${filename}";
      value.text = builtins.replaceStrings (builtins.elemAt subs 0) (builtins.elemAt subs 1) (
        builtins.readFile (workspaceInstructionsPath + "/${filename}")
      );
    }) filenames
  );
in
{
  home.file = files;
}
