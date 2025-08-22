{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.readItNow-rc.packages.${pkgs.system}.default
  ];
}
