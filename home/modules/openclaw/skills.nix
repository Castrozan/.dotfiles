{ config, ... }:
let
  workspacePath = config.openclaw.workspacePath;
  agentSkillsPath = ../../../agents/skills;

  skillDirNames = builtins.filter (name: (builtins.readDir agentSkillsPath).${name} == "directory") (
    builtins.attrNames (builtins.readDir agentSkillsPath)
  );

  skills = builtins.listToAttrs (
    builtins.concatMap (
      dirname:
      let
        skillDir = agentSkillsPath + "/${dirname}";
        entries = builtins.readDir skillDir;
        files = builtins.filter (name: entries.${name} == "regular") (builtins.attrNames entries);
      in
      map (file: {
        name = "${workspacePath}/skills/${dirname}/${file}";
        value.text = builtins.readFile (skillDir + "/${file}");
      }) files
    ) skillDirNames
  );
in
{
  home.file = skills;
}
