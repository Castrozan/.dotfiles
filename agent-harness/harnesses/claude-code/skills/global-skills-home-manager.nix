{ pkgs, hostname, ... }:
let
  projection = import ../../../agent-instructions/instruction-projection.nix { inherit pkgs; };
  interactiveAgentSkills =
    import ../../../agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix
      {
        inherit hostname;
        inherit pkgs;
      };

  claudeInteractiveSkillNames = interactiveAgentSkills.effectiveInteractiveSkillNames { };

  coreRulesDirectory = ../../../agent-instructions/core-rules;

  globalClaudeSkillDirectorySymlinks = interactiveAgentSkills.skillDirectorySymlinksAtPrefix ".claude/skills" claudeInteractiveSkillNames;

  makeGlobalSkillFromInstructionsFile =
    {
      skillName,
      skillDescription,
      instructionsFile,
    }:
    {
      ".claude/skills/${skillName}/SKILL.md".source = projection.instructionText {
        name = "claude-${skillName}-SKILL.md";
        deployed = "/.claude/skills/${skillName}/SKILL.md";
        destinations = { };
        text = ''
          ---
          name: ${skillName}
          description: ${skillDescription}
          ---

          ${builtins.readFile instructionsFile}
        '';
      };
    };

  coreSkillFromAgentInstructions = makeGlobalSkillFromInstructionsFile {
    skillName = "core";
    skillDescription = "Display core agent behavior instructions. Use when user wants to see, review, or reference the core rules, or when injecting core instructions as context into subagents, oneshot sessions, or external tools.";
    instructionsFile = coreRulesDirectory + "/core.md";
  };

  allSkillsIndexSkill = interactiveAgentSkills.renderAllSkillsIndexSkill claudeInteractiveSkillNames;

  allSkillsIndexSkillFile = {
    ".claude/skills/all-skills/SKILL.md".source = projection.instructionText {
      name = "claude-all-skills-SKILL.md";
      deployed = "/.claude/skills/all-skills/SKILL.md";
      destinations = interactiveAgentSkills.deploymentDestinations ".claude/skills" claudeInteractiveSkillNames;
      text = ''
        ---
        name: all-skills
        description: ${builtins.toJSON allSkillsIndexSkill.description}
        ---

        ${allSkillsIndexSkill.body}
      '';
    };
  };
in
{
  home.file =
    globalClaudeSkillDirectorySymlinks // coreSkillFromAgentInstructions // allSkillsIndexSkillFile;
}
