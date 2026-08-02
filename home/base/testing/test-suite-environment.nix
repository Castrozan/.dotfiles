{ pkgs }:
let
  pythonTestEnvironment = import ./python-test-environment.nix { inherit pkgs; };
in
pkgs.buildEnv {
  name = "dotfiles-test-suite-environment";
  paths = [
    pythonTestEnvironment
    pkgs.pyright
    pkgs.ripgrep
  ];
}
