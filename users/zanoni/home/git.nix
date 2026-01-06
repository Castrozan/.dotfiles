{ pkgs, ... }:
let
  gitconfig = builtins.readFile ../../../.gitconfig;
  userName = "Castrozan";
  userEmail = "castro.lucas290@gmail.com";
in
{
  home.packages = with pkgs; [
    gh
    delta
  ];

  programs.git = {
    enable = true;
    settings = {
      user.name = userName;
      user.email = userEmail;
    };
  };

  home.file.".gitconfig" = {
    text = ''
      ${gitconfig}

      [user]
        name  = ${userName}
        email = ${userEmail}
    '';
  };

  home.file.".githooks/commit-msg" = {
    source = ../../../.githooks/dotfiles-user-commit.sh;
    executable = true;
  };
}
