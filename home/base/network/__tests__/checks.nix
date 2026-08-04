{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../../../linux/network/network-optimization.nix
    ../tailscale-daemon.nix
  ];

  hasActivation = name: builtins.hasAttr name cfg.home.activation;
in
{
  domain-system-network-optimization =
    mkEvalCheck "domain-system-network-optimization" (hasActivation "setupNetworkOptimization")
      "network optimization activation should exist";
}
