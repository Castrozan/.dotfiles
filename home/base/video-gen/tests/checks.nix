{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  hasPackageNamed =
    needle: lib.any (package: lib.hasInfix needle (package.name or "")) cfg.home.packages;
in
{
  domain-video-gen-command =
    mkEvalCheck "domain-video-gen-command" (hasPackageNamed "video-gen")
      "video-gen wrapper command should be installed in home.packages";
}
