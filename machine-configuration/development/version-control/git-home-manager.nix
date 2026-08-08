{ pkgs, ... }:
let
  gitMessageEditor = pkgs.writeShellScript "git-message-editor" (
    builtins.readFile ./scripts/git-message-editor
  );
in
{
  imports = [ ../../../agent-harness/commit-provenance/commit-provenance-home-manager.nix ];

  home.packages = with pkgs; [
    gh
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
    };
  };
}
