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

  hasXdgConfig = name: builtins.hasAttr name cfg.xdg.configFile;
in
{
  domain-openclaw-mesh-config = mkEvalCheck "domain-openclaw-mesh-config" (
    hasXdgConfig "openclaw-mesh/config.json" && builtins.hasAttr "mesh" cfg.openclaw
  ) "openclaw-mesh should have config and options";
}
