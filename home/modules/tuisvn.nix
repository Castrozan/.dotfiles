{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.tuisvn.packages.${pkgs.system}.default
  ];
}
