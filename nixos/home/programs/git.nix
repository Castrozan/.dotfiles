{pkgs, ...}: {
  home.packages = [pkgs.gh];

  programs.git = {
    enable = true;

    # ... Other options ...
  };

  programs.git = {
    userName = "Castrozan";
    userEmail = "castro.lucas290@gmail.com";
  };
}
