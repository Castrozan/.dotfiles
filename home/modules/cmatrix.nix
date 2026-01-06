{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.cmatrix.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
