{ hostname, ... }:
let
  interactiveAgentSkills = import ../../../agents/interactive-agent-skills.nix { inherit hostname; };

  reachableSkillDirectorySymlinks = interactiveAgentSkills.skillDirectorySymlinksAtPrefix ".local/share/agent-skill-index" interactiveAgentSkills.allSkillNames;
in
{
  home.file = reachableSkillDirectorySymlinks;
}
