{ ... }:
let
  skillsDir = ../../../agents/skills;

  # Get all directories from the skills directory
  skillDirs = builtins.filter
    (name: builtins.pathExists (skillsDir + "/${name}/SKILL.md"))
    (builtins.attrNames (builtins.readDir skillsDir));

  # Create home.file entries for each skill directory
  skillSymlinks = builtins.listToAttrs (map
    (dirname: {
      name = ".claude/skills/${dirname}";
      value = {
        source = skillsDir + "/${dirname}";
        recursive = true;
      };
    })
    skillDirs);
in
{
  home.file = skillSymlinks;
}
