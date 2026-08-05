{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../oom-protection-home-manager.nix
  ];

  hasActivation = name: builtins.hasAttr name cfg.home.activation;
in
{
  domain-system-oom-protection =
    mkEvalCheck "domain-system-oom-protection" (hasActivation "setupOomProtection")
      "oom protection activation should exist";
}
