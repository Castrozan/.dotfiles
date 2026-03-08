{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.readItNow-rc.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
