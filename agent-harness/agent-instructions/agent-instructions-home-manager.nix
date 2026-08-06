{ pkgs, ... }:
let
  codingSkillInstall = import ./skills/coding/install {
    inherit pkgs;
  };
in
{
  imports = [
    ../agent-to-agent-communication/client/a2a-client-home-manager.nix
    ../session-control/agent-session-control-home-manager.nix
    ./repository-local-deployment/dotfiles-repo-agent-instructions-home-manager.nix
    ./repository-local-deployment/dotfiles-repo-skills-home-manager.nix
    ./interactive-skill-catalog/interactive-skill-index-home-manager.nix
    ./skills/twitter/install/twitter-home-manager.nix
    ./skills/phone-status/phone-status-cli-home-manager.nix
    ./skills/ril/install/ril-home-manager.nix
    ./skills/todo/install/todo-home-manager.nix
  ];

  home.packages = codingSkillInstall.packages;
}
