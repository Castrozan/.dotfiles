{ ... }:
{
  imports = [ ../../../home/modules/dev/git.nix ];

  programs.git = {
    userName = "Lucas de Castro Zanoni";
    userEmail = "lucas.zanoni@betha.com.br";
  };
}
