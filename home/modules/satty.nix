{ pkgs, ... }:
{
  home = {
    file.".config/satty".source = ../../.config/satty;

    packages = [
      pkgs.satty
    ];
  };
}
