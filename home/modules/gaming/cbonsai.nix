{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.cbonsai.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
