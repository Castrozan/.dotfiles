{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.install-nothing.packages.${pkgs.system}.default
  ];
}
