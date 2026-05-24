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

  cfg = helpers.homeManagerTestConfiguration [
    ../vesktop.nix
    ../cbonsai.nix
    ../cmatrix.nix
    ../install-nothing.nix
  ];

  hasFile = name: builtins.hasAttr name cfg.home.file;
in
{
  domain-gaming-vesktop-config =
    mkEvalCheck "domain-gaming-vesktop-config" (hasFile ".config/vesktop/settings/settings.json")
      "vesktop config should be deployed";
}
