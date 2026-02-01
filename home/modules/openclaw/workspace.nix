{
  lib,
  config,
  ...
}:
let
  ws = config.openclaw.workspace;
  agentDir = ../../../agents/openclaw;

  mdFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir agentDir)
  );

  contextFiles = builtins.listToAttrs (
    map (filename: {
      name = "${ws}/${filename}";
      value.text = builtins.readFile (agentDir + "/${filename}");
    }) mdFiles
  );
in
{
  options.openclaw.workspace = lib.mkOption {
    type = lib.types.str;
    default = "openclaw";
    description = "Workspace directory name relative to home";
  };

  config.home.file = contextFiles;
}
