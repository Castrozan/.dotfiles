{ pkgs, inputs, ... }:
{
  imports = [ ./devenv-container/devenv-container-home-manager.nix ];

  home.packages = [
    inputs.devenv.packages.${pkgs.stdenv.hostPlatform.system}.devenv
  ];
}
