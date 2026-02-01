{ lib, ... }:
let
  sharedSkillsDir = ../../../agents/skills;

  skillDirNames = builtins.filter (
    name: (builtins.readDir sharedSkillsDir).${name} == "directory"
  ) (builtins.attrNames (builtins.readDir sharedSkillsDir));

  # Symlink SKILL.md to .nix/skills/ (read-only reference)
  nixSkillSymlinks = builtins.listToAttrs (
    map (dirname: {
      name = "clawd/.nix/skills/${dirname}/SKILL.md";
      value.source = sharedSkillsDir + "/${dirname}/SKILL.md";
    }) skillDirNames
  );

  # Symlink SKILL.md to skills/ (workspace-visible)
  workspaceSkillSymlinks = builtins.listToAttrs (
    builtins.concatMap (
      dirname:
      let
        skillDir = sharedSkillsDir + "/${dirname}";
        entries = builtins.readDir skillDir;
        files = builtins.filter (name: entries.${name} == "regular") (builtins.attrNames entries);
      in
      map (file: {
        name = "clawd/skills/${dirname}/${file}";
        value.source = skillDir + "/${file}";
      }) files
    ) skillDirNames
  );
in
{
  home.file = nixSkillSymlinks // workspaceSkillSymlinks;
}
