{ lib, ... }:
let
  sharedRulesDir = ../../../agents/rules;

  rulesFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir sharedRulesDir)
  );

  rulesSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "clawd/.nix/rules/${filename}";
      value = {
        source = sharedRulesDir + "/${filename}";
      };
    }) rulesFiles
  );
in
{
  home.file = rulesSymlinks;
}
