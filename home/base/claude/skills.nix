{ pkgs, ... }:
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

  interactivePreferencesRawContent = builtins.readFile ../../../agents/interactive-preferences.md;

  interactivePreferencesSkillFromInstructions = {
    ".claude/skills/interactive-preferences/SKILL.md".text = ''
      ---
      name: interactive-preferences
      description: Inject Lucas's interactive-session response preferences (TL;DR-only replies; exhaust capabilities before returning) into the running session as governing rules. Use when a session was started without these rules in its system prompt - an already-running session, or one not launched via the cla/claude wrapper - and Lucas asks to apply, load, or inject his interactive preferences.
      ---

      ${interactivePreferencesRawContent}
    '';
  };

  skillNamesWithInstallModule = builtins.filter (
    skillName: builtins.pathExists (dotfilesSkillsDirectory + "/${skillName}/install/default.nix")
  ) allSkillNames;

  installModuleAcceptsOnlyPkgs =
    skillName:
    let
      installModule = import (dotfilesSkillsDirectory + "/${skillName}/install");
      installModuleArgs = builtins.functionArgs installModule;
    in
    builtins.length (builtins.attrNames installModuleArgs) == 1 && installModuleArgs ? pkgs;

  skillNamesAutoWiredHere = builtins.filter installModuleAcceptsOnlyPkgs skillNamesWithInstallModule;

  packagesFromSkillInstallModules = builtins.concatLists (
    map (
      skillName:
      let
        installModule = import (dotfilesSkillsDirectory + "/${skillName}/install") { inherit pkgs; };
      in
      installModule.packages or [ ]
    ) skillNamesAutoWiredHere
  );
in
{
  home = {
    file =
      baseGloballyLoadedClaudeSkills
      // personalVaultClaudeSkills
      // coreSkillFromAgentInstructions
      // interactivePreferencesSkillFromInstructions;
    packages = packagesFromSkillInstallModules;
  };
}
