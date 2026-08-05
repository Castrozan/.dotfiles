{ hostname }:
let
  publicSkillsDirectory = ../skills;
  privateSharedSkillsDirectory = ../../../private-configuration/claude/skills;
  privateMachineSkillsDirectory = ../../../private-configuration/machines + "/${hostname}/skills";

  skillSourceDirectories = builtins.filter builtins.pathExists [
    publicSkillsDirectory
    privateSharedSkillsDirectory
    privateMachineSkillsDirectory
  ];

  completeSkillNamesIn =
    skillSourceDirectory:
    builtins.filter (skillName: builtins.pathExists (skillSourceDirectory + "/${skillName}/SKILL.md")) (
      builtins.attrNames (builtins.readDir skillSourceDirectory)
    );

  skillSourceDirectoryByName = builtins.foldl' (
    accumulatedSourceDirectoryByName: skillSourceDirectory:
    accumulatedSourceDirectoryByName
    // builtins.listToAttrs (
      map (skillName: {
        name = skillName;
        value = skillSourceDirectory + "/${skillName}";
      }) (completeSkillNamesIn skillSourceDirectory)
    )
  ) { } skillSourceDirectories;

  allSkillNames = builtins.attrNames skillSourceDirectoryByName;

  skillDirectorySymlinksAtPrefix =
    homeFileSkillsPrefix: skillNames:
    builtins.listToAttrs (
      map (skillName: {
        name = "${homeFileSkillsPrefix}/${skillName}";
        value = {
          source = skillSourceDirectoryByName.${skillName};
        };
      }) skillNames
    );
in
{
  inherit
    allSkillNames
    skillSourceDirectoryByName
    skillDirectorySymlinksAtPrefix
    ;
}
