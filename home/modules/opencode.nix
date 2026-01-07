{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.opencode.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
