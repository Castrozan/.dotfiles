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

  tailscaleDaemonActivation = cfg.home.activation.checkTailscaleDaemon.data;

  tailscaleDaemonLocationsThisRepoInstallsTo = [
    "/run/current-system/sw/bin/tailscaled"
    "/etc/profiles/per-user/test/bin/tailscaled"
    "/opt/homebrew/bin/tailscaled"
  ];
in
{
  domain-system-network-optimization =
    mkEvalCheck "domain-system-network-optimization" (hasActivation "setupNetworkOptimization")
      "network optimization activation should exist";

  domain-network-tailscale-daemon-probes-every-install-location =
    mkEvalCheck "domain-network-tailscale-daemon-probes-every-install-location"
      (builtins.all (
        location: lib.hasInfix location tailscaleDaemonActivation
      ) tailscaleDaemonLocationsThisRepoInstallsTo)
      "the tailscale daemon check must probe each location this repo installs tailscaled to: the nix system profile for services.tailscale.enable on NixOS and nix-darwin, the per-user profile for the home-manager user package, and the homebrew prefix for a homebrew.brews entry — home-manager activation runs on a closed PATH that reaches none of them, so probing by PATH alone reports a running daemon as missing";

  domain-network-tailscale-daemon-must-not-end-the-activation-run =
    mkEvalCheck "domain-network-tailscale-daemon-must-not-end-the-activation-run"
      (!lib.hasInfix "exit " tailscaleDaemonActivation)
      "home-manager concatenates every activation snippet into one script, so an exit here would silently skip every later activation step including linkGeneration";
}
