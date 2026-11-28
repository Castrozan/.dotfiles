{
  inputs,
  hostname,
  pkgs,
  ...
}:
let
  personalRepositoryForge = "github";
  personalRepositoryRouting = import ./personal-repository-routing.nix personalRepositoryForge;
  gitMessageEditor = pkgs.writeShellScript "git-message-editor" (
    builtins.readFile ./scripts/git-message-editor
  );
in
{
  imports = [
    inputs.commit-provenance.homeManagerModules.default
    ./github-home-manager.nix
  ];

  programs.commit-provenance = {
    machineName = hostname;
    sessionControlPythonPath = ../../../agent-harness/session-control;
  };

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
    ignores = [
      ".claude-context"
      ".worktrees/"
      ".deep-work/"
    ];
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
      url = personalRepositoryRouting;
    };
  };
}
