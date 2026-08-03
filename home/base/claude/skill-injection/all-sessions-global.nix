_:
let
  skillSetBuilders = import ../../../../agents/skill-set-builders.nix;
  interactiveAgentSkills = import ../../../../agents/interactive-agent-skills.nix;

  claudeInteractiveSkillNames = interactiveAgentSkills.effectiveInteractiveSkillNames {
    add = [ "housekeeping" ];
  };

  coreRulesDirectory = ../../../../agents/core_rules;

  globalClaudeSkillDirectorySymlinks = skillSetBuilders.claudeSkillDirectorySymlinksAtPrefix ".claude/skills" claudeInteractiveSkillNames;

  readInstructionsBodyWithoutFrontmatter =
    instructionsFile:
    let
      rawInstructionsContent = builtins.readFile instructionsFile;
      startsWithFrontmatterDelimiter = builtins.substring 0 4 rawInstructionsContent == "---\n";
    in
    if startsWithFrontmatterDelimiter then
      builtins.elemAt (builtins.split "---\n" rawInstructionsContent) 4
    else
      rawInstructionsContent;

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

        ${readInstructionsBodyWithoutFrontmatter instructionsFile}
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
