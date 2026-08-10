{
  helpers,
  pkgs,
  lib,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  cfg = helpers.homeManagerTestConfiguration [ self.homeManagerModules.default ];
  cfgOnTheEvaluatingSystem = helpers.homeManagerTestConfigurationForEvaluatingSystem [
    self.homeManagerModules.default
  ];
  exportedHarnessModules = [
    self.homeManagerModules.claude-code
    self.homeManagerModules.clawde
    self.homeManagerModules.codex
    self.homeManagerModules.opencode
  ];
  packageNamesFor =
    configuration: map (package: package.name or package.pname or "") configuration.home.packages;
  deploysAgentSession = configuration: builtins.elem "agent-session" (packageNamesFor configuration);
  deploysGitHistory = configuration: builtins.elem "git-history" (packageNamesFor configuration);

  interactiveAgentSkills = import ../interactive-skill-catalog/interactive-agent-skills.nix {
    hostname = "test";
  };

  harnessProjectSkillDirectoriesInRepository = [
    ".claude/skills"
    ".opencode/skills"
  ];

  everyRepositorySkillDirectoryCarriesTheRepoLocalSkills = builtins.all (
    pathInRepository:
    builtins.all (
      skillName: builtins.hasAttr ".dotfiles/${pathInRepository}/${skillName}" cfg.home.file
    ) interactiveAgentSkills.dotfilesRepoSkillNames
  ) harnessProjectSkillDirectoriesInRepository;

  interactiveSkillCatalogContainsEveryCuratedSkill = builtins.all (
    skillName: builtins.elem skillName interactiveAgentSkills.allSkillNames
  ) interactiveAgentSkills.defaultInteractiveSkillNames;

  dotfilesCheckoutAgentInstructionFilesAreDeclared =
    builtins.hasAttr ".dotfiles/AGENTS.md" cfgOnTheEvaluatingSystem.home.file
    && builtins.hasAttr ".dotfiles/CLAUDE.md" cfgOnTheEvaluatingSystem.home.file
    &&
      cfgOnTheEvaluatingSystem.home.file.".dotfiles/AGENTS.md".text
      == cfgOnTheEvaluatingSystem.home.file.".dotfiles/CLAUDE.md".text;

  globalCoreInstructions = builtins.readFile ../core-rules/core.md;
  normalizedGlobalCoreInstructions = lib.toLower globalCoreInstructions;
  globalCoreMaximumBytes = 5000;
  globalCoreForbiddenFragments = [
    ".dotfiles"
    "heartbeat.md"
    "nixos"
    "`nix"
    "obsidian"
    "second brain"
    "webfetch"
    "gh run"
    "git agent-session"
    "claude-gpt"
    "claude code"
    "codex"
    "opencode"
    "herdr"
    "a2a "
    "/compact"
    "--resume"
    "rebuild"
    "python 3.12"
  ];
  globalCoreContainsOnlyUniversalPolicy = builtins.all (
    fragment: !(lib.hasInfix fragment normalizedGlobalCoreInstructions)
  ) globalCoreForbiddenFragments;
in
{
  default-home-manager-module-deploys-agent-session =
    mkEvalCheck "default-home-manager-module-deploys-agent-session"
      (deploysAgentSession cfgOnTheEvaluatingSystem && dotfilesCheckoutAgentInstructionFilesAreDeclared)
      "the default exported Home Manager module must install agent-session and deploy identical AGENTS.md and CLAUDE.md into the dotfiles checkout so every harness reads the same project context";

  standalone-harness-modules-deploy-agent-session =
    mkEvalCheck "standalone-harness-modules-deploy-agent-session"
      (builtins.all deploysAgentSession (
        map (module: helpers.homeManagerTestConfiguration [ module ]) exportedHarnessModules
      ))
      "every standalone harness module must install agent-session because the restart skill and the exit path both invoke it";

  dotfiles-repo-skills-deploy-into-every-project-skill-directory =
    mkEvalCheck "dotfiles-repo-skills-deploy-into-every-project-skill-directory"
      (
        interactiveSkillCatalogContainsEveryCuratedSkill
        && everyRepositorySkillDirectoryCarriesTheRepoLocalSkills
      )
      "the interactive skill catalog must resolve every curated skill and deploy every repo-local skill into each harness project skill directory inside the dotfiles checkout";

  harness-modules-deploy-git-history = mkEvalCheck "harness-modules-deploy-git-history" (builtins.all
    deploysGitHistory
    (map (module: helpers.homeManagerTestConfiguration [ module ]) exportedHarnessModules)
  ) "every harness module that deploys coding must install its git-history executable";

  global-core-stays-universal =
    mkEvalCheck "global-core-stays-universal"
      (
        builtins.stringLength globalCoreInstructions <= globalCoreMaximumBytes
        && globalCoreContainsOnlyUniversalPolicy
      )
      "core.md must stay below the global context budget and contain only cross-harness, cross-domain policy; move repository, harness, tool, and capability mechanics to their owning surfaces";
}
