{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.tuisvn.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
