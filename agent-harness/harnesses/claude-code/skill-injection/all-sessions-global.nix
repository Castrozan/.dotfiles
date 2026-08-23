{ hostname, ... }:
let
  interactiveAgentSkills =
    import
      ../../../../agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix
      {
        inherit hostname;
      };

  claudeInteractiveSkillNames = interactiveAgentSkills.effectiveInteractiveSkillNames { };

  coreRulesDirectory = ../../../../agent-harness/agent-instructions/core-rules;

  globalClaudeSkillDirectorySymlinks = interactiveAgentSkills.skillDirectorySymlinksAtPrefix ".claude/skills" claudeInteractiveSkillNames;

  makeGlobalSkillFromInstructionsFile =
    {
      skillName,
      skillDescription,
      instructionsFile,
    }:
    {
      ".claude/skills/${skillName}/SKILL.md".text = ''
        ---
        name: ${skillName}
        description: ${skillDescription}
        ---

        ${builtins.readFile instructionsFile}
      '';
    };

  coreSkillFromAgentInstructions = makeGlobalSkillFromInstructionsFile {
    skillName = "core";
    skillDescription = "Display core agent behavior instructions. Use when user wants to see, review, or reference the core rules, or when injecting core instructions as context into subagents, oneshot sessions, or external tools.";
    instructionsFile = coreRulesDirectory + "/core.md";
  };

  allSkillsIndexSkill = interactiveAgentSkills.renderAllSkillsIndexSkill claudeInteractiveSkillNames;

  allSkillsIndexSkillFile = {
    ".claude/skills/all-skills/SKILL.md".text = ''
      ---
      name: all-skills
      description: ${allSkillsIndexSkill.description}
      ---

      ${allSkillsIndexSkill.body}
    '';
  };
in
{
  home.file =
    globalClaudeSkillDirectorySymlinks // coreSkillFromAgentInstructions // allSkillsIndexSkillFile;
}
