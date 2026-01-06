{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.install-nothing.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
