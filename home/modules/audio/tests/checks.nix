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

  hasService = name: builtins.hasAttr name cfg.systemd.user.services;
in
{
  domain-audio-bluetooth-service =
    mkEvalCheck "domain-audio-bluetooth-service" (hasService "bluetooth-audio-autoswitch")
      "bluetooth audio autoswitch service should exist";
}
