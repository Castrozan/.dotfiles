{ ... }:
{
  imports = [ ../../../home/modules/dev/git.nix ];

  programs.git.settings.user = {
    name = "Castrozan";
    email = "castro.lucas290@gmail.com";
  };
}
