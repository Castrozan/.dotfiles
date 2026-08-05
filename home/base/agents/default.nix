{ pkgs, ... }:
let
  codingSkillInstall = import ../../../agents/skills/coding/install { inherit pkgs; };
in
{
  imports = [
    ./a2a
    ./agent-session-control.nix
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
