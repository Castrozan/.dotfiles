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

  makeSkillFromInstructionsFile =
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

  coreSkillFromAgentInstructions = makeSkillFromInstructionsFile {
    skillName = "core";
    skillDescription = "Display core agent behavior instructions. Use when user wants to see, review, or reference the core rules, or when injecting core instructions as context into subagents, oneshot sessions, or external tools.";
    instructionsFile = ../../../agents/core.md;
  };

  interactivePreferencesSkillFromInstructions = makeSkillFromInstructionsFile {
    skillName = "interactive-preferences";
    skillDescription = "Inject Lucas's interactive-session response preferences (TL;DR-only replies; exhaust capabilities before returning) into the running session as governing rules. Use when a session was started without these rules in its system prompt - an already-running session, or one not launched via the cla/claude wrapper - and Lucas asks to apply, load, or inject his interactive preferences.";
    instructionsFile = ../../../agents/interactive-preferences.md;
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
