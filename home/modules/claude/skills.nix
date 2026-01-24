_:
let
  dotfilesSkillsDir = ../../../agents/skills;

  getSkillNamesFromDir =
    dir:
    if builtins.pathExists dir then
      builtins.filter (name: builtins.pathExists (dir + "/${name}/SKILL.md")) (
        builtins.attrNames (builtins.readDir dir)
      )
    else
      [ ];

  skillNames = getSkillNamesFromDir dotfilesSkillsDir;

  globalClaudeSkills = builtins.listToAttrs (
    map (dirname: {
      name = ".claude/skills/${dirname}";
      value = {
        source = dotfilesSkillsDir + "/${dirname}";
        recursive = true;
      };
    }) skillNames
  );
in
{
  # Create symlinks for global Claude skills
  home.file = globalClaudeSkills;
}
