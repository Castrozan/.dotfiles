{ lib, ... }:
let
  sharedSkillsDir = ../../../agents/skills;

  skillDirNames = builtins.filter (
    name: (builtins.readDir sharedSkillsDir).${name} == "directory"
  ) (builtins.attrNames (builtins.readDir sharedSkillsDir));

  workspaceSkillEntries = builtins.listToAttrs (
    builtins.concatMap (
      dirname:
      let
        skillDir = sharedSkillsDir + "/${dirname}";
        entries = builtins.readDir skillDir;
        files = builtins.filter (name: entries.${name} == "regular") (builtins.attrNames entries);
      in
      map (file: {
        name = "clawd/skills/${dirname}/${file}";
        value.text = builtins.readFile (skillDir + "/${file}");
      }) files
    ) skillDirNames
  );
in
{
  home.file = workspaceSkillEntries;
}
