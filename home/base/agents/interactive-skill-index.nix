{ hostname, ... }:
let
  interactiveAgentSkills =
    import
      ../../../agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix
      { inherit hostname; };

  reachableSkillDirectorySymlinks = interactiveAgentSkills.skillDirectorySymlinksAtPrefix ".local/share/agent-skill-index" interactiveAgentSkills.reachableSkillNames;
in
{
  home.file = reachableSkillDirectorySymlinks;
}
