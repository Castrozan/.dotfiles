{ lib, ... }:
let
  sharedRulesDir = ../../../agents/rules;

  rulesFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir sharedRulesDir)
  );

  rulesEntries = builtins.listToAttrs (
    map (filename: {
      name = "clawd/rules/${filename}";
      value.text = builtins.readFile (sharedRulesDir + "/${filename}");
    }) rulesFiles
  );
in
{
  home.file = rulesEntries;
}
