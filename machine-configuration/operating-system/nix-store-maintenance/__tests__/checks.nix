{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../stale-symlink-cleanup-home-manager.nix
  ];

  hasActivation = name: builtins.hasAttr name cfg.home.activation;
in
{
  domain-system-stale-symlink-cleanup =
    mkEvalCheck "domain-system-stale-symlink-cleanup" (hasActivation "removeStaleNixStoreSymlinks")
      "stale nix store symlink cleanup activation should exist";
}
