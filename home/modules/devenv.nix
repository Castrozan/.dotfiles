{ pkgs, inputs, ... }:
{
  # Pinned to v1.9.2 in flake.nix - latest version is broken
  home.packages = [
    inputs.devenv.packages.${pkgs.stdenv.hostPlatform.system}.devenv
  ];
}
