{
  lib,
  config,
  ...
}:
let
  workspacePath = config.openclaw.workspace;
  wsInstructionsPath = ../../../agents/openclaw/workspace;

  filenames = (builtins.attrNames (builtins.readDir wsInstructionsPath));

  files = builtins.listToAttrs (
    map (filename: {
      name = "${workspacePath}/${filename}";
      value.text = builtins.readFile (wsInstructionsPath + "/${filename}");
    }) filenames
  );
in
{
  options.openclaw.workspace = lib.mkOption {
    type = lib.types.str;
    default = "openclaw";
    description = "Workspace directory path relative to home";
  };

  home.file = files;
}
