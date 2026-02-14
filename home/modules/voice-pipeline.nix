{ pkgs, ... }:
{
  imports = [
    ../../voice-pipeline/nix/package.nix
    ../../voice-pipeline/nix/module.nix
  ];
}
