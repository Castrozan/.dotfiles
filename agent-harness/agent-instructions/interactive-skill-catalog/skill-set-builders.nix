{ hostname }:
let
  publicSkillsDirectory = ../skills;
  privateSharedSkillsDirectory = ../../../private-configuration/agent-harness/claude/skills;
  privateMachineSkillsDirectory = ../../../private-configuration/machines + "/${hostname}/skills";

  presentDirectories = builtins.filter builtins.pathExists;

  privateSkillSourceDirectories = presentDirectories [
    privateSharedSkillsDirectory
    privateMachineSkillsDirectory
  ];

  skillSourceDirectories =
    presentDirectories [
      publicSkillsDirectory
    ]
    ++ privateSkillSourceDirectories;

  completeSkillNamesIn =
    skillSourceDirectory:
    builtins.filter (skillName: builtins.pathExists (skillSourceDirectory + "/${skillName}/SKILL.md")) (
      builtins.attrNames (builtins.readDir skillSourceDirectory)
    );

  privateSkillNames = builtins.concatMap completeSkillNamesIn privateSkillSourceDirectories;

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
    privateSkillNames
    skillSourceDirectoryByName
    skillDirectorySymlinksAtPrefix
    ;
}
