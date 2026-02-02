{ lib, config, ... }:
let
  openclaw = config.openclaw;
  scriptsSourcePath = ../../../agents/scripts;

  filenames = builtins.filter (name: lib.hasSuffix ".sh" name || lib.hasSuffix ".py" name) (
    builtins.attrNames (builtins.readDir scriptsSourcePath)
  );

  files = builtins.listToAttrs (
    map (filename: {
      name = "scripts/${filename}";
      value = {
        text = openclaw.substituteAgentConfig (scriptsSourcePath + "/${filename}");
        executable = true;
      };
    }) filenames
  );
in
{
  home.file = openclaw.deployToWorkspace files;
}
