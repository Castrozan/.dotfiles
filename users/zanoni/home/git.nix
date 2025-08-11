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
    userName = userName;
    userEmail = userEmail;
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
