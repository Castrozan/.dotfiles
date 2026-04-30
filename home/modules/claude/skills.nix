{
  ...
}:
let
  dotfilesSkillsDirectory = ../../../agents/skills;

  globallyLoadedSkillNames = [ "personal" ];

  getSkillNamesFromDirectory =
    directory:
    if builtins.pathExists directory then
      builtins.filter (skillName: builtins.pathExists (directory + "/${skillName}/SKILL.md")) (
        builtins.attrNames (builtins.readDir directory)
      )
    else
      [ ];

  allSkillNames = getSkillNamesFromDirectory dotfilesSkillsDirectory;

  baseGloballyLoadedSkillNames = builtins.filter (
    skillName: builtins.elem skillName globallyLoadedSkillNames
  ) allSkillNames;

  personalVaultSkillNames = builtins.filter (
    skillName: !builtins.elem skillName globallyLoadedSkillNames
  ) allSkillNames;

  baseGloballyLoadedClaudeSkills = builtins.listToAttrs (
    map (skillDirectoryName: {
      name = ".claude/skills/${skillDirectoryName}";
      value = {
        source = dotfilesSkillsDirectory + "/${skillDirectoryName}";
        recursive = true;
      };
    }) baseGloballyLoadedSkillNames
  );

  personalVaultClaudeSkills = builtins.listToAttrs (
    map (skillDirectoryName: {
      name = ".local/share/claude-skill-sets/personal/.claude/skills/${skillDirectoryName}";
      value = {
        source = dotfilesSkillsDirectory + "/${skillDirectoryName}";
        recursive = true;
      };
    }) personalVaultSkillNames
  );

  coreAgentRawContent = builtins.readFile ../../../agents/core.md;
  coreAgentSplitOnFrontmatterDelimiter = builtins.split "---\n" coreAgentRawContent;
  coreAgentBodyWithoutFrontmatter = builtins.elemAt coreAgentSplitOnFrontmatterDelimiter 4;

  coreSkillFromAgentInstructions = {
    ".claude/skills/core/SKILL.md".text = ''
      ---
      name: core
      description: Display core agent behavior instructions. Use when user wants to see, review, or reference the core rules, or when injecting core instructions as context into subagents, oneshot sessions, or external tools.
      ---

      ${coreAgentBodyWithoutFrontmatter}
    '';
  };
in
{
  home.file =
    baseGloballyLoadedClaudeSkills // personalVaultClaudeSkills // coreSkillFromAgentInstructions;
}
