{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.google-workspace-cli.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
