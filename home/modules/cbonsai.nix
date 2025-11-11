{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.cbonsai.packages.${pkgs.system}.default
  ];
}
