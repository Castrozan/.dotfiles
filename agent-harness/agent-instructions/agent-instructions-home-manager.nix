{
  hostname ? "",
  inputs,
  pkgs,
  ...
}:
let
  codingSkillInstall = import ./skills/development/coding/install {
    inherit pkgs;
  };
in
{
  imports = [
    ../plugin-distribution/home-manager.nix
    ./production-plugin/home-manager.nix
    ../agent-to-agent-communication/client/a2a-client-home-manager.nix
    inputs.orchestrator.homeManagerModules.default
    ../servants/servants-home-manager.nix
    ../session-control/agent-session-control-home-manager.nix
    ../workflows/workflows-home-manager.nix
    ./dotfiles-checkout-agent-surfaces/dotfiles-repo-agent-instructions-home-manager.nix
    ./dotfiles-checkout-agent-surfaces/dotfiles-repo-skills-home-manager.nix
    ./skills/media/twitter/install/twitter-home-manager.nix
    ./skills/services/phone-status/phone-status-cli-home-manager.nix
    ./skills/services/url-shortener/url-shortener-cli-home-manager.nix
    inputs.read-it-later.homeManagerModules.default
    ./skills/knowledge/todo/install/todo-home-manager.nix
  ];

  programs.orchestrator.userModelPath = "~/.dotfiles/private-configuration/agent-harness/user-model/USER.md";

  programs.ril = {
    forgePythonPath = ./skills/development/forge/scripts;
    machineName = hostname;
    repositoryName = ".dotfiles";
  };

  home.packages = codingSkillInstall.packages;
}
