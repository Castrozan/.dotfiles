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
    ../lid-switch-ignore.nix
    ../oom-protection.nix
  ];

  hasActivation = name: builtins.hasAttr name cfg.home.activation;
in
{
  domain-system-oom-protection =
    mkEvalCheck "domain-system-oom-protection" (hasActivation "setupOomProtection")
      "oom protection activation should exist";

  domain-system-lid-switch =
    mkEvalCheck "domain-system-lid-switch" (hasActivation "setupLidSwitchIgnore")
      "lid switch ignore activation should exist";
}
