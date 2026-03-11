{ ... }:
{
  imports = [ ../../../home/modules/dev/git.nix ];

  programs.git.settings.user = {
    name = "Lucas de Castro Zanoni";
    email = "lucas.zanoni@dev.pro";
  };
}
