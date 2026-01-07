{ pkgs, ... }:
let
  gitconfig = builtins.readFile ../../../.gitconfig;
  userName = "Lucas de Castro Zanoni";
  userEmail = "lucas.zanoni@betha.com.br";
in
{
  home.packages = with pkgs; [
    gh
    delta
  ];

  programs.git = {
    enable = true;
    settings = {
      user = {
        name = userName;
        email = userEmail;
      };
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
