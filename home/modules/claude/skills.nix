{
  config,
  lib,
  ...
}:
let
  dotfilesSkillsDir = ../../../agents/skills;

  getSkillNamesFromDir =
    dir:
    if builtins.pathExists dir then
      builtins.filter (name: builtins.pathExists (dir + "/${name}/SKILL.md")) (
        builtins.attrNames (builtins.readDir dir)
      )
    else
      [ ];

  skillNames = getSkillNamesFromDir dotfilesSkillsDir;

  openclawModuleIsAvailable = builtins.hasAttr "openclaw" config;

  skillsThatRequireOpenclawInfrastructure = [
    "openclaw"
    "grid"
    "assistant-cron"
    "hey-clever"
  ];

  skillNamesWithoutPlatformExclusions =
    if openclawModuleIsAvailable then
      skillNames
    else
      builtins.filter (name: !builtins.elem name skillsThatRequireOpenclawInfrastructure) skillNames;

  personalOnlySkills = import ./personal-only-skills.nix;

  baseSkillNames = builtins.filter (
    name: !builtins.elem name personalOnlySkills
  ) skillNamesWithoutPlatformExclusions;

  personalOnlySkillNames = builtins.filter (
    name: builtins.elem name personalOnlySkills
  ) skillNamesWithoutPlatformExclusions;

  baseClaudeSkills = builtins.listToAttrs (
    map (dirname: {
      name = ".claude/skills/${dirname}";
      value = {
        source = dotfilesSkillsDir + "/${dirname}";
        recursive = true;
      };
    }) baseSkillNames
  );

  personalOnlyClaudeSkills = builtins.listToAttrs (
    map (dirname: {
      name = ".local/share/claude-skill-sets/personal/.claude/skills/${dirname}";
      value = {
        source = dotfilesSkillsDir + "/${dirname}";
        recursive = true;
      };
    }) personalOnlySkillNames
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
  home.file = baseClaudeSkills // personalOnlyClaudeSkills // coreSkillFromAgentInstructions;
}
