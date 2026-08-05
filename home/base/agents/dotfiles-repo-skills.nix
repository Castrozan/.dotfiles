{ hostname, ... }:
let
  interactiveAgentSkills = import ../../../agents/interactive-agent-skills.nix { inherit hostname; };

  harnessProjectSkillDirectories = [
    {
      pathInRepository = ".claude/skills";
      deploysEachSkillFileSeparately = false;
    }
    {
      pathInRepository = ".opencode/skills";
      deploysEachSkillFileSeparately = true;
    }
  ];

  repositorySkillSymlinksIn =
    {
      pathInRepository,
      deploysEachSkillFileSeparately,
    }:
    builtins.listToAttrs (
      map (skillName: {
        name = ".dotfiles/${pathInRepository}/${skillName}";
        value = {
          source = interactiveAgentSkills.skillSourceDirectoryByName.${skillName};
          recursive = deploysEachSkillFileSeparately;
        };
      }) interactiveAgentSkills.dotfilesRepoSkillNames
    );
in
{
  home.file = builtins.foldl' (
    accumulated: harnessProjectSkillDirectory:
    accumulated // repositorySkillSymlinksIn harnessProjectSkillDirectory
  ) { } harnessProjectSkillDirectories;
}
