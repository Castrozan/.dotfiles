{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../network-optimization/network-optimization-home-manager.nix
    ../tailscale/tailscale-daemon-home-manager.nix
  ];

  hasActivation = name: builtins.hasAttr name cfg.home.activation;
in
{
  domain-system-network-optimization =
    mkEvalCheck "domain-system-network-optimization" (hasActivation "setupNetworkOptimization")
      "network optimization activation should exist";
}
