_:
let
  skillSetBuilders = import ../../../agents/skill-set-builders.nix;
  interactiveAgentSkills = import ../../../agents/interactive-agent-skills.nix;

  codexInteractiveSkillNames = interactiveAgentSkills.effectiveInteractiveSkillNames {
    add = [ "browser" ];
  };

  coreAgentRawContent = builtins.readFile ../../../agents/core_rules/core.md;
  coreAgentSplitOnFrontmatterDelimiter = builtins.split "---\n" coreAgentRawContent;
  coreAgentBodyWithoutFrontmatter = builtins.elemAt coreAgentSplitOnFrontmatterDelimiter 4;

  codexSkillLinks = skillSetBuilders.claudeSkillDirectorySymlinksAtPrefix ".codex/skills" codexInteractiveSkillNames;

  coreSkillFromAgentInstructions = {
    ".codex/skills/core/SKILL.md".text = ''
      ---
      name: core
      description: Display core agent behavior instructions. Use when user wants to see, review, or reference the core rules, or when injecting core instructions as context into subagents, oneshot sessions, or external tools.
      ---

      ${coreAgentBodyWithoutFrontmatter}
    '';
  };

  allSkillsIndexSkill = interactiveAgentSkills.renderAllSkillsIndexSkill codexInteractiveSkillNames;

  allSkillsIndexSkillFile = {
    ".codex/skills/all-skills/SKILL.md".text = ''
      ---
      name: all-skills
      description: ${allSkillsIndexSkill.description}
      ---

      ${allSkillsIndexSkill.body}
    '';
  };

in
{
  home.file = codexSkillLinks // coreSkillFromAgentInstructions // allSkillsIndexSkillFile;
}
