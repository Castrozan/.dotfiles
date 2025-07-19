{ pkgs, ... }:
{
  home.packages = [
    pkgs.gh
    pkgs.delta
  ];

  programs.git = {
    enable = true;
    userName = "Castrozan";
    userEmail = "castro.lucas290@gmail.com";

    extraConfig = {
      core.pager = "delta";
      interactive.diffFilter = "delta --color-only";
      delta.navigate = true; # use n/N to jump hunks
      delta.dark = true; # force dark theme
      merge.conflictstyle = "zdiff3";
    };
  };
}
