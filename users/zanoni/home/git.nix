{ ... }:
{
  imports = [ ../../../home/modules/dev/git.nix ];

  programs.git = {
    userName = "Castrozan";
    userEmail = "castro.lucas290@gmail.com";
  };
}
