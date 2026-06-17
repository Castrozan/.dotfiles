_:
let
  skillSetBuilders = import ./skill-set-builders.nix;

  personalSkillSetClaudeSkillDirectorySymlinks = skillSetBuilders.claudeSkillDirectorySymlinksAtPrefix ".local/share/claude-skill-sets/personal/.claude/skills" skillSetBuilders.specializedSkillSetSkillNames;

  curatedSkillSets = {
    steward = [
      "git"
      "nix"
      "test"
      "deep-work"
      "workspace"
      "worktrees"
      "tmux"
      "exit"
      "restart"
      "notify"
      "review"
    ];
  };

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
  home.file =
    personalSkillSetClaudeSkillDirectorySymlinks // allCuratedSkillSetClaudeSkillDirectorySymlinks;
}
