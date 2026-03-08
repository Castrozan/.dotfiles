{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.bluetui.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
