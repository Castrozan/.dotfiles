{ ... }:
{
  imports = [ ../../../development/version-control/git-home-manager.nix ];

  programs.git.settings.user = {
    name = "Castrozan";
    email = "castro.lucas290@gmail.com";
  };
}
