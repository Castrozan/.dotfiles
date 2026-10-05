{ pkgs, ... }:
let
  gitMessageEditor = pkgs.writeShellScript "git-message-editor" (
    builtins.readFile ./scripts/git-message-editor
  );
in
{
  imports = [
    ../../../agent-harness/commit-provenance/commit-provenance-home-manager.nix
    ./github-home-manager.nix
  ];

  home.packages = with pkgs; [
    delta
  ];

  home.file = {
    ".githooks/commit-msg" = {
      source = ../../../repository/git-hooks/scope-commit.sh;
      executable = true;
    };
  };

  programs.git = {
    enable = true;
    ignores = [ ".claude-context" ];
    settings = {
      core = {
        pager = "delta --paging=never --detect-dark-light always";
        hooksPath = "~/.githooks";
        editor = "${gitMessageEditor}";
      };
      alias.fzf = "!git-fzf";
      interactive.diffFilter = "delta --color-only --paging=never --detect-dark-light always";
      delta = {
        navigate = false;
        line-numbers = true;
        syntax-theme = "Monokai Extended";
        dark = true;
      };
      diff.context = 5;
      url = {
        "git@github.com:Castrozan/.dotfiles.git".insteadOf = [
          "git@gitlab.com:Castrozan/dotfiles.git"
          "https://gitlab.com/Castrozan/dotfiles.git"
        ];
        "git@github.com:Castrozan/dotfiles-private.git".insteadOf = [
          "git@gitlab.com:Castrozan/dotfiles-private.git"
          "https://gitlab.com/Castrozan/dotfiles-private.git"
        ];
        "git@github.com:Castrozan/zanoni-system.git".insteadOf = [
          "git@gitlab.com:Castrozan/zanoni-system.git"
          "https://gitlab.com/Castrozan/zanoni-system.git"
        ];
      };
    };
  };
}
