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

  globalOpencodeSkills = builtins.listToAttrs (
    map (dirname: {
      name = ".config/opencode/skills/${dirname}";
      value = {
        source = dotfilesSkillsDir + "/${dirname}";
        recursive = true;
      };
    }) skillNames
  );
in
{
  home.file = globalOpencodeSkills;
}
