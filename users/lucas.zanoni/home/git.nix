{ pkgs, ... }:
let
  gitconfig = builtins.readFile ../../../.gitconfig;
  userName = "Lucas de Castro Zanoni";
  userEmail = "lucas.zanoni@betha.com.br";
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
        source = ../../../.githooks/scope-commit.sh;
        executable = true;
      };
    };
  };

  programs.git = {
    enable = true;
    ignores = [ ".claude-context" ];
    settings = {
      user = {
        name = userName;
        email = userEmail;
      };
    };
  };
}
