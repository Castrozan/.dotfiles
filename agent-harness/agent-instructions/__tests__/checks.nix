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
    inherit pkgs;
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

  everyRepositorySkillUsesTheCompletePackage = builtins.all (
    pathInRepository:
    builtins.all (
      skillName:
      let
        entry = cfg.home.file.".dotfiles/${pathInRepository}/${skillName}";
      in
      toString entry.source == "${cfg.agentPlugins.bundle}/plugin/library/skills/${skillName}"
      && !entry.recursive
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
    && !(builtins.hasAttr ".dotfiles/CLAUDE.md" cfgOnTheEvaluatingSystem.home.file);

  globalCoreInstructions = builtins.readFile ../core-rules/core.md;
  normalizedGlobalCoreInstructions = lib.toLower globalCoreInstructions;
  globalCoreHasNoFrontmatter = !(lib.hasPrefix "---\n" globalCoreInstructions);
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
    "### Evidence"
    "### Autonomy"
    "### Completion"
    "### Delegation"
    "### Context"
    "### Coding"
    "### Instruction placement"
  ];
  globalCoreRetiredAuthorityFragments = [
    "### Judgment"
    "### Ownership"
    "### Skills"
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
    fragment: !(lib.hasInfix (lib.toLower fragment) normalizedGlobalCoreInstructions)
  ) globalCoreRetiredAuthorityFragments;
in
{
  default-home-manager-module-deploys-agent-session =
    mkEvalCheck "default-home-manager-module-deploys-agent-session"
      (deploysAgentSession cfgOnTheEvaluatingSystem && dotfilesCheckoutAgentInstructionFilesAreDeclared)
      "the default exported Home Manager module must install agent-session and deploy AGENTS.md alone into the dotfiles checkout, because every harness including Claude reads it natively and a CLAUDE.md beside it would make Claude ignore it";

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
        && everyRepositorySkillUsesTheCompletePackage
      )
      "the interactive skill catalog must resolve every curated skill and link every repo-local skill directory directly to the complete plugin package inside each harness project skill directory";

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
        && globalCoreHasNoFrontmatter
        && globalCoreContainsOnlyUniversalPolicy
        && globalCoreContainsEveryRequiredSection
        && globalCoreContainsNoRetiredAuthority
      )
      "core.md must contain only plain universal session-long policy below the global context budget, including conditionally triggered coding behavior; keep metadata, repository, harness, tool, and bounded procedure mechanics in their owning surfaces";
}
// import ./generated-instruction-checks.nix { inherit pkgs lib; }
