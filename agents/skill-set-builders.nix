let
  dotfilesSkillsDirectory = ./skills;

  getSkillNamesFromDirectory =
    directory:
    if builtins.pathExists directory then
      builtins.filter (skillName: builtins.pathExists (directory + "/${skillName}/SKILL.md")) (
        builtins.attrNames (builtins.readDir directory)
      )
    else
      [ ];

  allSkillNames = getSkillNamesFromDirectory dotfilesSkillsDirectory;

  claudeSkillDirectorySymlinksAtPrefix =
    homeFileSkillsPrefix: skillNames:
    builtins.listToAttrs (
      map (skillDirectoryName: {
        name = "${homeFileSkillsPrefix}/${skillDirectoryName}";
        value = {
          source = dotfilesSkillsDirectory + "/${skillDirectoryName}";
        };
      }) skillNames
    );
in
{
  inherit
    dotfilesSkillsDirectory
    allSkillNames
    claudeSkillDirectorySymlinksAtPrefix
    ;
}
