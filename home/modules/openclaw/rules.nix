{ lib, config, ... }:
let
  ws = config.openclaw.workspace;
  sharedRulesDir = ../../../agents/rules;

  rulesFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir sharedRulesDir)
  );

  rulesEntries = builtins.listToAttrs (
    map (filename: {
      name = "${ws}/rules/${filename}";
      value.text = builtins.readFile (sharedRulesDir + "/${filename}");
    }) rulesFiles
  );
in
{
  home.file = rulesEntries;
}
