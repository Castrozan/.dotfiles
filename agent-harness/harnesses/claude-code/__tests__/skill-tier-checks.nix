{
  pkgs,
  lib,
  mkEvalCheck,
  cfg,
  hasFilePrefix,
}:
let
  interactiveAgentSkills =
    import
      ../../../../agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix
      {
        hostname = "test";
        inherit pkgs;
      };

  claudeInteractiveSkillNames = interactiveAgentSkills.effectiveInteractiveSkillNames { };

  staysOffEveryGlobalSurface =
    skillName:
    !(builtins.hasAttr ".claude/skills/${skillName}" cfg.home.file)
    && !(builtins.hasAttr ".local/share/agent-skill-index/${skillName}" cfg.home.file)
    && !(builtins.elem skillName (
      interactiveAgentSkills.indexedSkillNamesFor claudeInteractiveSkillNames
    ));

  uninjectedSkillsStayOutOfEverySurface = builtins.all staysOffEveryGlobalSurface interactiveAgentSkills.uninjectedSkillNames;

  dotfilesRepoSkillsStayOutOfEverySurface = builtins.all staysOffEveryGlobalSurface interactiveAgentSkills.dotfilesRepoSkillNames;

  privateMachinesDirectory = ../../../../private-configuration/machines;

  privateMachineNames =
    if builtins.pathExists privateMachinesDirectory then
      builtins.attrNames (builtins.readDir privateMachinesDirectory)
    else
      [ ];

  privateMachineSkillNamesFor =
    machineName:
    let
      privateMachineSkillsDirectory = privateMachinesDirectory + "/${machineName}/skills";
    in
    if builtins.pathExists privateMachineSkillsDirectory then
      builtins.filter (
        skillName: builtins.pathExists (privateMachineSkillsDirectory + "/${skillName}/SKILL.md")
      ) (builtins.attrNames (builtins.readDir privateMachineSkillsDirectory))
    else
      [ ];

  everyPrivateMachineSkillIsCatalogued = builtins.all (
    machineName:
    let
      cataloguedSkillNames =
        (import
          ../../../../agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix
          {
            hostname = machineName;
            inherit pkgs;
          }
        ).allSkillNames;
    in
    builtins.all (skillName: builtins.elem skillName cataloguedSkillNames) (
      privateMachineSkillNamesFor machineName
    )
  ) privateMachineNames;
in
{
  claude-production-plugin-registration =
    mkEvalCheck "claude-production-plugin-registration"
      (
        builtins.hasAttr "installProductionClaudePlugin" cfg.home.activation
        && builtins.hasAttr ".local/share/agent-plugins/dotfiles" cfg.home.file
        && !(hasFilePrefix ".claude/skills/")
      )
      "Claude must register the complete production package without duplicate managed global skill projections";

  claude-retired-skill-mirror = mkEvalCheck "claude-retired-skill-mirror" (
    !(hasFilePrefix ".local/share/agent-skill-index/")
  ) "Indexed skills must resolve inside the complete package without a second source projection";

  claude-uninjected-skills-reach-no-global-surface =
    mkEvalCheck "claude-uninjected-skills-reach-no-global-surface" uninjectedSkillsStayOutOfEverySurface
      "a private skill its machine's indexed-skill-names.nix does not name must stay out of the machine tier, out of the all-skills index and out of the reachability mirror; it exists for the one agent that declares it by path, and any of those three surfaces would put it back in every session's budget";

  claude-dotfiles-repo-skills-reach-no-global-surface =
    mkEvalCheck "claude-dotfiles-repo-skills-reach-no-global-surface"
      dotfilesRepoSkillsStayOutOfEverySurface
      "a skill named in dotfilesRepoSkillNames describes the dotfiles tree alone and must stay out of the machine tier, out of the all-skills index and out of the reachability mirror; it reaches an agent through the repository's own project skill directories, and any global surface would charge every unrelated session for it";

  claude-private-machine-skills-are-catalogued =
    mkEvalCheck "claude-private-machine-skills-are-catalogued" everyPrivateMachineSkillIsCatalogued
      "every private-configuration/machines/<hostname>/skills skill must be enumerated by the shared catalog for that hostname; a private root the catalog never reads is either injected behind the curated list's back or missing from the all-skills index entirely";
}
