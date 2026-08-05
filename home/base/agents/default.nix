{ pkgs, ... }:
let
  codingSkillInstall = import ../../../agent-harness/agent-instructions/skills/coding/install {
    inherit pkgs;
  };
in
{
  imports = [
    ../../../agent-harness/agent-to-agent-communication/client/a2a-client-home-manager.nix
    ../../../agent-harness/session-control/agent-session-control-home-manager.nix
    ./dotfiles-repo-agent-instructions.nix
    ./dotfiles-repo-skills.nix
    ./interactive-skill-index.nix
    ./twitter-cli.nix
    ./phone-status-cli.nix
    ./ril-cli.nix
    ./todo-cli.nix
  ];

  home.packages = codingSkillInstall.packages;
}
