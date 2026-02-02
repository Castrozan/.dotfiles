{ config, ... }:
let
  openclaw = config.openclaw;
  rulesSourcePath = ../../../agents/rules;

  filenames = builtins.attrNames (builtins.readDir rulesSourcePath);

  files = builtins.listToAttrs (
    map (filename: {
      name = "rules/${filename}";
      value.text = openclaw.substituteAgentConfig (rulesSourcePath + "/${filename}");
    }) filenames
  );
in
{
  home.file = openclaw.deployToBoth files;
}
