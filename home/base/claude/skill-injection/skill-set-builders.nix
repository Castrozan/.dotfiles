let
  dotfilesSkillsDirectory = ../../../../agents/skills;

  globallyLoadedSkillNames = [
    "personal"
    "goal-prompt"
    "browser"
    "deliver"
    "tmux-claude"
    "instructions"
    "review"
    "humanize"
    "restart"
  ];

  getSkillNamesFromDirectory =
    directory:
    if builtins.pathExists directory then
      builtins.filter (skillName: builtins.pathExists (directory + "/${skillName}/SKILL.md")) (
        builtins.attrNames (builtins.readDir directory)
      )
    else
      [ ];

  allSkillNames = getSkillNamesFromDirectory dotfilesSkillsDirectory;

  globallyLoadedSkillNamesPresentOnDisk = builtins.filter (
    skillName: builtins.elem skillName globallyLoadedSkillNames
  ) allSkillNames;

  specializedSkillSetSkillNames = builtins.filter (
    skillName: !builtins.elem skillName globallyLoadedSkillNames
  ) allSkillNames;

  claudeSkillDirectorySymlinksAtPrefix =
    homeFileSkillsPrefix: skillNames:
    builtins.listToAttrs (
      map (skillDirectoryName: {
        name = "${homeFileSkillsPrefix}/${skillDirectoryName}";
        value = {
          source = dotfilesSkillsDirectory + "/${skillDirectoryName}";
          recursive = true;
        };
      }) skillNames
    );
in
{
  inherit
    dotfilesSkillsDirectory
    allSkillNames
    globallyLoadedSkillNamesPresentOnDisk
    specializedSkillSetSkillNames
    claudeSkillDirectorySymlinksAtPrefix
    ;
}
