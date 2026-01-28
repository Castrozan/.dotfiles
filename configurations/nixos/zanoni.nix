{
  inputs,
  pkgs,
  lib,
  username,
  unstable,
  latest,
  home-version,
  nixpkgs-version,
  ...
}:
{
  imports = [
    ../../hosts/dellg15
    ../../users/${username}/nixos.nix
  ];
}
