{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.devenv.packages.${pkgs.stdenv.hostPlatform.system}.devenv
  ];
}
