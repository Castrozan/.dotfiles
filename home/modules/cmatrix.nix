{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.cmatrix.packages.${pkgs.system}.default
  ];
}
