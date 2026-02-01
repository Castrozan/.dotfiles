{ lib, config, ... }:
let
  workspacePath = config.openclaw.workspacePath;
  scriptsPath = ../../../agents/scripts;

  filenames = builtins.filter (name: lib.hasSuffix ".sh" name || lib.hasSuffix ".py" name) (
    builtins.attrNames (builtins.readDir scriptsPath)
  );

  scripts = builtins.listToAttrs (
    map (filename: {
      name = "${workspacePath}/scripts/${filename}";
      value.source = scriptsPath + "/${filename}";
    }) filenames
  );
in
{
  home.file = scripts;
}
