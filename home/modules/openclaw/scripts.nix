{ lib, config, ... }:
let
  openclaw = config.openclaw;
  scriptsSourcePath = ../../../agents/scripts;

  filenames = builtins.filter (name: lib.hasSuffix ".sh" name || lib.hasSuffix ".py" name) (
    builtins.attrNames (builtins.readDir scriptsSourcePath)
  );

  scriptFiles = builtins.listToAttrs (
    map (filename: {
      name = "${openclaw.workspacePath}/scripts/${filename}";
      value = {
        text = openclaw.templateFile (scriptsSourcePath + "/${filename}");
        executable = true;
      };
    }) filenames
  );
in
{
  home.file = scriptFiles;
}
