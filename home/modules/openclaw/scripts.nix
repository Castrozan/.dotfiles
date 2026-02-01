{ lib, config, ... }:
let
  cfg = config.openclaw;
  workspacePath = cfg.workspacePath;
  scriptsPath = ../../../agents/scripts;
  subs = cfg.substitutions;

  filenames = builtins.filter (name: lib.hasSuffix ".sh" name || lib.hasSuffix ".py" name) (
    builtins.attrNames (builtins.readDir scriptsPath)
  );

  scripts = builtins.listToAttrs (
    map (filename: {
      name = "${workspacePath}/scripts/${filename}";
      value = {
        text = builtins.replaceStrings (builtins.elemAt subs 0) (builtins.elemAt subs 1) (
          builtins.readFile (scriptsPath + "/${filename}")
        );
        executable = true;
      };
    }) filenames
  );
in
{
  home.file = scripts;
}
