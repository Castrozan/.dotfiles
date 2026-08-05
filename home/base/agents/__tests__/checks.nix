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

  interactiveAgentSkills = import ../../../../agents/interactive-agent-skills.nix {
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

  dotfilesRepositoryDiscoveryLinkSourcesAreDeclared =
    builtins.hasAttr ".dotfiles/.githooks" cfgOnTheEvaluatingSystem.home.file
    && builtins.hasAttr ".dotfiles/.vscode" cfgOnTheEvaluatingSystem.home.file;
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
        test "$(readlink ${
          cfgOnTheEvaluatingSystem.home.file.".dotfiles/.vscode".source
        })" = "/home/test/.dotfiles/repository/visual-studio-code-workspace"
        touch $out
      ''
    else
      builtins.throw "CHECK FAILED [default-home-manager-module-deploys-agent-session]: the default exported Home Manager module must install agent-session and declare the repository discovery links consumed by agent and editor tooling";

  standalone-harness-modules-deploy-agent-session =
    mkEvalCheck "standalone-harness-modules-deploy-agent-session"
      (builtins.all deploysAgentSession (
        map (module: helpers.homeManagerTestConfiguration [ module ]) exportedHarnessModules
      ))
      "every standalone harness module must install agent-session because the restart skill and the exit path both invoke it";

  dotfiles-repo-skills-deploy-into-every-project-skill-directory =
    mkEvalCheck "dotfiles-repo-skills-deploy-into-every-project-skill-directory"
      everyRepositorySkillDirectoryCarriesTheRepoLocalSkills
      "every repo-local skill must deploy into each harness project skill directory inside the dotfiles checkout; these skills reach no global surface, so a missing project directory strands them for that harness entirely";

  harness-modules-deploy-git-history = mkEvalCheck "harness-modules-deploy-git-history" (builtins.all
    deploysGitHistory
    (map (module: helpers.homeManagerTestConfiguration [ module ]) exportedHarnessModules)
  ) "every harness module that deploys coding must install its git-history executable";
}
