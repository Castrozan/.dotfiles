{ config, ... }:
let
  workspacePath = config.openclaw.workspacePath;
  agentRulesDirectory = ../../../agents/rules;

  ruleFileNames = (builtins.attrNames (builtins.readDir agentRulesDirectory));

  rules = builtins.listToAttrs (
    map (filename: {
      name = "${workspacePath}/rules/${filename}";
      value.text = builtins.readFile (agentRulesDirectory + "/${filename}");
    }) ruleFileNames
  );
in
{
  home.file = rules;
}
