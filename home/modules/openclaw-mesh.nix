{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.openclaw-mesh.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
