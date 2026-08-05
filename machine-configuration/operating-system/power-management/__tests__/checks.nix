{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../lid-switch-ignore-home-manager.nix
  ];

  hasActivation = name: builtins.hasAttr name cfg.home.activation;
in
{
  domain-system-lid-switch =
    mkEvalCheck "domain-system-lid-switch" (hasActivation "setupLidSwitchIgnore")
      "lid switch ignore activation should exist";
}
