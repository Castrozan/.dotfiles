_:
let
  sharedSkillsDir = ../../../agents/skills;

  skillDirNames = builtins.filter (name: (builtins.readDir sharedSkillsDir).${name} == "directory") (
    builtins.attrNames (builtins.readDir sharedSkillsDir)
  );

  skillsSymlinks = builtins.listToAttrs (
    map (dirname: {
      name = "clawd/.nix/skills/${dirname}/SKILL.md";
      value = {
        source = sharedSkillsDir + "/${dirname}/SKILL.md";
      };
    }) skillDirNames
  );
in
{
  home.file = skillsSymlinks;
}
