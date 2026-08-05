{ pkgs, ... }:
{
  home = {
    file.".config/satty".source = ./program-configuration/satty;

    packages = [
      pkgs.satty
    ];
  };
}
