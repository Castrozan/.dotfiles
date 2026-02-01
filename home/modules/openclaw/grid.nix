{ lib, ... }:
let
  openclawAgentDir = ../../../agents/openclaw;
  sharedScriptsDir = ../../../agents/scripts;

  gridSymlinks = {
    "clawd/GRID.md" = {
      source = openclawAgentDir + "/grid.md";
    };
  };

  scriptFiles = builtins.filter (
    name: lib.hasSuffix ".sh" name || lib.hasSuffix ".py" name
  ) (builtins.attrNames (builtins.readDir sharedScriptsDir));

  scriptsSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "clawd/scripts/${filename}";
      value = {
        source = sharedScriptsDir + "/${filename}";
      };
    }) scriptFiles
  );
in
{
  home.file = gridSymlinks // scriptsSymlinks;
}
