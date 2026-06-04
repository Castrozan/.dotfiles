_:
let
  skillSetBuilders = import ./skill-set-builders.nix;

  coreRulesDirectory = ../../../../agents/core_rules;

  globalClaudeSkillDirectorySymlinks = skillSetBuilders.claudeSkillDirectorySymlinksAtPrefix ".claude/skills" skillSetBuilders.globallyLoadedSkillNamesPresentOnDisk;

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

  interactivePreferencesSkillFromInstructions = makeGlobalSkillFromInstructionsFile {
    skillName = "interactive-preferences";
    skillDescription = "Inject Lucas's interactive-session response preferences (TL;DR-only replies; exhaust capabilities before returning) into the running session as governing rules. Use when a session was started without these rules in its system prompt - an already-running session, or one not launched via the cla/claude wrapper - and Lucas asks to apply, load, or inject his interactive preferences.";
    instructionsFile = coreRulesDirectory + "/communication/interactive-preferences.md";
  };
in
{
  home.file =
    globalClaudeSkillDirectorySymlinks
    // coreSkillFromAgentInstructions
    // interactivePreferencesSkillFromInstructions;
}
