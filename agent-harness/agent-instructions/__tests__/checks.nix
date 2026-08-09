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

  dotfilesRepositoryDiscoveryLinkSourcesAreDeclared = builtins.hasAttr ".dotfiles/.githooks" cfgOnTheEvaluatingSystem.home.file;
in
{
  default-home-manager-module-deploys-agent-session =
    if
      deploysAgentSession cfgOnTheEvaluatingSystem && dotfilesRepositoryDiscoveryLinkSourcesAreDeclared
    then
      pkgs.runCommandLocal "check-default-home-manager-module-deploys-agent-session" { } ''
        test "$(readlink ${
          cfgOnTheEvaluatingSystem.home.file.".dotfiles/.githooks".source
        })" = "/home/test/.dotfiles/repository/git-hooks"
        touch $out
      ''
    else
      builtins.throw "CHECK FAILED [default-home-manager-module-deploys-agent-session]: the default exported Home Manager module must install agent-session and declare the repository discovery links consumed by agent tooling";

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
}
