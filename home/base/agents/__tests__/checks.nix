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
in
{
  default-home-manager-module-deploys-agent-session =
    mkEvalCheck "default-home-manager-module-deploys-agent-session" (deploysAgentSession cfg)
      "the default exported Home Manager module must install agent-session because the restart skill and the exit path both invoke it";

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
