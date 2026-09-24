{
  pkgs,
  hostname,
  config,
  lib,
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

  home.activation.retireRepositorySkillBackups = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    ${pkgs.python312}/bin/python3 ${../production-plugin/scripts/retire-projections.py} \
      repository "${config.home.homeDirectory}" ${config.agentPlugins.bundle}
  '';

  home.file = builtins.foldl' (
    accumulated: harnessProjectSkillDirectory:
    accumulated // repositorySkillSymlinksIn harnessProjectSkillDirectory
  ) { } harnessProjectSkillDirectories;
}
