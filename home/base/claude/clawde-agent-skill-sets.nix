{ config, lib, ... }:
let
  skillSetBuilders = import ./skill-injection/skill-set-builders.nix;

  personalSkillSetClaudeSkillDirectorySymlinks = skillSetBuilders.claudeSkillDirectorySymlinksAtPrefix ".local/share/claude-skill-sets/personal/.claude/skills" skillSetBuilders.specializedSkillSetSkillNames;

  curatedSkillSets = config.claudeCuratedSkillSets;

  curatedSkillSetClaudeSkillDirectorySymlinks =
    setName: skillNames:
    skillSetBuilders.claudeSkillDirectorySymlinksAtPrefix
      ".local/share/claude-skill-sets/${setName}/.claude/skills"
      (builtins.filter (skillName: builtins.elem skillName skillSetBuilders.allSkillNames) skillNames);

  allCuratedSkillSetClaudeSkillDirectorySymlinks = builtins.foldl' (
    accumulated: setName:
    accumulated // curatedSkillSetClaudeSkillDirectorySymlinks setName curatedSkillSets.${setName}
  ) { } (builtins.attrNames curatedSkillSets);
in
{
  options.claudeCuratedSkillSets = lib.mkOption {
    type = lib.types.attrsOf (lib.types.listOf lib.types.str);
    default = { };
    description = ''
      Named subsets of the dotfiles skills, each materialized at
      .local/share/claude-skill-sets/<set>/.claude/skills for a clawde agent to
      load with --add-dir. The clawde flake hardcodes that layout for the
      steward set, so the path is an interface, not an internal detail. Declare
      a set from the module that owns the agent consuming it, not here, so the
      skill list stays next to the agent whose job defines it. A name matching
      no skill on disk is dropped rather than failing the build, so a set
      survives a skill rename until someone notices the agent lost it.
    '';
  };

  config.home.file =
    personalSkillSetClaudeSkillDirectorySymlinks // allCuratedSkillSetClaudeSkillDirectorySymlinks;
}
