{
  pkgs,
  hostname,
  config,
  ...
}:
let
  interactiveAgentSkills = import ../interactive-skill-catalog/interactive-agent-skills.nix {
    inherit hostname;
    inherit pkgs;
  };

  harnessProjectSkillDirectories = [
    ".claude/skills"
    ".opencode/skills"
  ];

  repositorySkillSymlinksIn =
    pathInRepository:
    builtins.listToAttrs (
      map (skillName: {
        name = ".dotfiles/${pathInRepository}/${skillName}";
        value = {
          source = "${config.agentPlugins.bundle}/plugin/library/skills/${skillName}";
        };
      }) interactiveAgentSkills.dotfilesRepoSkillNames
    );
in
{
  imports = [ ../production-plugin/home-manager.nix ];

  home.file = builtins.foldl' (
    accumulated: harnessProjectSkillDirectory:
    accumulated // repositorySkillSymlinksIn harnessProjectSkillDirectory
  ) { } harnessProjectSkillDirectories;
}
