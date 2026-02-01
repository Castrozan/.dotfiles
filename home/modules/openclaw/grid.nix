{ lib, config, ... }:
let
  ws = config.openclaw.workspace;
  sharedScriptsDir = ../../../agents/scripts;

  scriptFiles = builtins.filter (
    name: lib.hasSuffix ".sh" name || lib.hasSuffix ".py" name
  ) (builtins.attrNames (builtins.readDir sharedScriptsDir));

  scriptsSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "${ws}/scripts/${filename}";
      value.source = sharedScriptsDir + "/${filename}";
    }) scriptFiles
  );
in
{
  home.file = scriptsSymlinks;
}
