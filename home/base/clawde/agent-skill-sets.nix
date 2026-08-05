{
  config,
  hostname,
  lib,
  ...
}:
let
  interactiveAgentSkills = import ../../../agents/interactive-agent-skills.nix { inherit hostname; };

  agentSkillSets = config.clawdeAgentSkillSets;

  normalHarnessSkillSetName = "normal-harness";

  agentSkillSetSkillDirectorySymlinks =
    setName: skillNames:
    interactiveAgentSkills.skillDirectorySymlinksAtPrefix
      ".local/share/claude-skill-sets/${setName}/.claude/skills"
      (
        builtins.filter (skillName: builtins.elem skillName interactiveAgentSkills.allSkillNames) skillNames
      );

  allAgentSkillSetSkillDirectorySymlinks = builtins.foldl' (
    accumulated: setName:
    accumulated // agentSkillSetSkillDirectorySymlinks setName agentSkillSets.${setName}
  ) { } (builtins.attrNames agentSkillSets);

  agentSkillSetDirectories = lib.mapAttrs (
    setName: _: "${config.home.homeDirectory}/.local/share/claude-skill-sets/${setName}"
  ) agentSkillSets;
in
{
  options.clawdeAgentSkillSets = lib.mkOption {
    type = lib.types.attrsOf (lib.types.listOf lib.types.str);
    default = { };
    description = ''
      Named subsets of the dotfiles skills, each materialized at
      .local/share/claude-skill-sets/<set>/.claude/skills for a clawde agent to
      load through skillDirectories, whichever harness it runs. The clawde flake
      hardcodes that path for the steward set, so it is an interface rather than
      an internal detail. Declare a set from the module that owns the agent
      consuming it, not here, so the skill list stays next to the agent whose job
      defines it. A name matching no skill on disk is dropped rather than failing
      the build, so a set survives a skill rename until someone notices the agent
      lost it.
    '';
  };

  options.clawdeAgentSkillSetDirectories = lib.mkOption {
    type = lib.types.attrsOf lib.types.str;
    readOnly = true;
    default = agentSkillSetDirectories;
    description = ''
      Directory each declared skill set materializes at, keyed by set name, for
      an agent to hand to skillDirectories without restating the layout.
    '';
  };

  options.normalHarnessSkillSetDirectory = lib.mkOption {
    type = lib.types.str;
    readOnly = true;
    default = agentSkillSetDirectories.${normalHarnessSkillSetName};
    description = ''
      Directory carrying the same skills an interactive session gets, for an
      agent whose job is whatever a keyboard session would do. An agent that
      already runs the claude harness inherits these from the machine tier and
      loses nothing by naming this too, since a set overlapping the machine tier
      collapses to one entry; naming it is what keeps the skills when the agent
      is switched onto a harness that reads no machine tier.
    '';
  };

  config = {
    clawdeAgentSkillSets.${normalHarnessSkillSetName} =
      interactiveAgentSkills.defaultInteractiveSkillNames;

    home.file = allAgentSkillSetSkillDirectorySymlinks;
  };
}
