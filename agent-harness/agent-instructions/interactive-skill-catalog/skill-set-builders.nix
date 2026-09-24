{
  hostname,
  pkgs,
  defaultInteractiveSkillNames,
}:
let
  projection = import ../instruction-projection.nix { inherit pkgs; };
  publicSkillSourceDirectories = [
    ../skills/agent-workflows
    ../skills/development
    ../skills/knowledge
    ../skills/media
    ../skills/services
    ../skills/workstation
    ../skills/writing
  ];
  privateSharedSkillsDirectory = ../../../private-configuration/agent-harness/claude/skills;
  privateMachineSkillsDirectory = ../../../private-configuration/machines + "/${hostname}/skills";

  presentDirectories = builtins.filter builtins.pathExists;

  privateSkillSourceDirectories = presentDirectories [
    privateSharedSkillsDirectory
    privateMachineSkillsDirectory
  ];

  skillSourceDirectories = publicSkillSourceDirectories ++ privateSkillSourceDirectories;

  completeSkillNamesIn =
    skillSourceDirectory:
    builtins.filter (skillName: builtins.pathExists (skillSourceDirectory + "/${skillName}/SKILL.md")) (
      builtins.attrNames (builtins.readDir skillSourceDirectory)
    );

  privateSkillNames = builtins.concatMap completeSkillNamesIn privateSkillSourceDirectories;
  publicSkillNames = builtins.concatMap completeSkillNamesIn publicSkillSourceDirectories;

  skillSourceDirectoryByName =
    assert builtins.length publicSkillNames == builtins.length (pkgs.lib.unique publicSkillNames);
    builtins.foldl' (
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

  deploymentDestinations =
    homeFileSkillsPrefix: skillNames:
    let
      indexed = builtins.listToAttrs (
        map (skillName: {
          name = toString skillSourceDirectoryByName.${skillName};
          value = "/.local/share/agent-plugins/dotfiles/plugin/${
            if builtins.elem skillName defaultInteractiveSkillNames then "skills" else "library/skills"
          }/${skillName}";
        }) allSkillNames
      );
      selected = builtins.listToAttrs (
        map (skillName: {
          name = toString skillSourceDirectoryByName.${skillName};
          value = "/${homeFileSkillsPrefix}/${skillName}";
        }) skillNames
      );
    in
    indexed
    // selected
    // {
      "${toString ../core-rules/core.md}" =
        "/.local/share/agent-plugins/dotfiles/plugin/skills/core/SKILL.md";
    };

  deployedSkillDirectory =
    homeFileSkillsPrefix: skillNames: skillName:
    let
      skillDirectory = projection.skillDirectory {
        source = skillSourceDirectoryByName.${skillName};
        deployed = "/${homeFileSkillsPrefix}/${skillName}";
        destinations = deploymentDestinations homeFileSkillsPrefix skillNames;
      };
    in
    if skillName == "research" then
      import ../skills/knowledge/research/pulse/install.nix { inherit pkgs skillDirectory; }
    else
      skillDirectory;

  skillDirectorySymlinksAtPrefix =
    homeFileSkillsPrefix: skillNames:
    builtins.listToAttrs (
      map (skillName: {
        name = "${homeFileSkillsPrefix}/${skillName}";
        value = {
          source = deployedSkillDirectory homeFileSkillsPrefix skillNames skillName;
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
    deployedSkillDirectory
    deploymentDestinations
    ;
}
