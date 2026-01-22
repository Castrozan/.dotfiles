{ pkgs, ... }:
let
  gitconfig = builtins.readFile ../../../.gitconfig;
  userName = "Castrozan";
  userEmail = "castro.lucas290@gmail.com";
in
{
  home = {
    packages = with pkgs; [
      gh
      delta
    ];

    file = {
      ".gitconfig".text = ''
        ${gitconfig}

        [user]
          name  = ${userName}
          email = ${userEmail}
      '';

      ".githooks/commit-msg" = {
        source = ../../../.githooks/dotfiles-user-commit.sh;
        executable = true;
      };
    };
  };

  programs.git = {
    enable = true;
    ignores = [ ".claude-context" ];
    settings = {
      user.name = userName;
      user.email = userEmail;
    };
  };
}
