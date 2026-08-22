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

  generatedAllSkillsDescription =
    (interactiveAgentSkills.renderAllSkillsIndexSkill interactiveAgentSkills.defaultInteractiveSkillNames)
    .description;
  skillRoutingEvaluationSurface = builtins.readFile ../../quality/evaluations/evals/skill_routing.yaml;
  skillRoutingEvaluationUsesGeneratedAllSkillsDescription = lib.hasInfix generatedAllSkillsDescription skillRoutingEvaluationSurface;

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
    "claudex"
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
  globalCoreRequiredSections = [
    "<evidence>"
    "<autonomy>"
    "<completion>"
    "<delegation>"
    "<context>"
    "<coding>"
    "<instruction-placement>"
  ];
  globalCoreRetiredAuthorityFragments = [
    "<judgment>"
    "<ownership>"
    "<skills>"
    "<mandatory-skill-routes>"
    "let it own the domain-specific policy"
    "keep the full policy in that skill"
  ];
  globalCoreContainsOnlyUniversalPolicy = builtins.all (
    fragment: !(lib.hasInfix fragment normalizedGlobalCoreInstructions)
  ) globalCoreForbiddenFragments;
  globalCoreContainsEveryRequiredSection = builtins.all (
    section: lib.hasInfix section globalCoreInstructions
  ) globalCoreRequiredSections;
  globalCoreContainsNoRetiredAuthority = builtins.all (
    fragment: !(lib.hasInfix fragment normalizedGlobalCoreInstructions)
  ) globalCoreRetiredAuthorityFragments;
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
      "every standalone harness module must install agent-session because the agent-session skill drives both restart and exit through it";

  dotfiles-repo-skills-deploy-into-every-project-skill-directory =
    mkEvalCheck "dotfiles-repo-skills-deploy-into-every-project-skill-directory"
      (
        interactiveSkillCatalogContainsEveryCuratedSkill
        && everyRepositorySkillDirectoryCarriesTheRepoLocalSkills
      )
      "the interactive skill catalog must resolve every curated skill and deploy every repo-local skill into each harness project skill directory inside the dotfiles checkout";

  skill-routing-evaluation-matches-generated-all-skills-catalog =
    mkEvalCheck "skill-routing-evaluation-matches-generated-all-skills-catalog"
      skillRoutingEvaluationUsesGeneratedAllSkillsDescription
      "the routing evaluation must use the generated all-skills description so indexed capabilities cannot drift from the deployed catalog";

  harness-modules-deploy-git-history = mkEvalCheck "harness-modules-deploy-git-history" (builtins.all
    deploysGitHistory
    (map (module: helpers.homeManagerTestConfiguration [ module ]) exportedHarnessModules)
  ) "every harness module that deploys coding must install its git-history executable";

  global-core-stays-universal =
    mkEvalCheck "global-core-stays-universal"
      (
        builtins.stringLength globalCoreInstructions <= globalCoreMaximumBytes
        && globalCoreContainsOnlyUniversalPolicy
        && globalCoreContainsEveryRequiredSection
        && globalCoreContainsNoRetiredAuthority
      )
      "core.md must stay below the global context budget and contain the required universal session-long policy, including conditionally triggered coding behavior; keep repository, harness, tool, and bounded procedure mechanics in their owning surfaces";
}
