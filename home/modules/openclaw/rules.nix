{ config, ... }:
let
  openclaw = config.openclaw;
  rulesSourcePath = ../../../agents/rules;

  filenames = builtins.attrNames (builtins.readDir rulesSourcePath);

  ruleFiles = builtins.listToAttrs (
    map (filename: {
      name = "${openclaw.workspacePath}/rules/${filename}";
      value.text = openclaw.substituteAgentConfig (rulesSourcePath + "/${filename}");
    }) filenames
  );
in
{
  home.file = ruleFiles;
}
