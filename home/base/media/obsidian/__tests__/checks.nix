{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../../__tests__/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../headless-sync.nix ];

  obsidianHeadlessNpmInstallActivation = cfg.home.activation.installObsidianHeadlessViaNpm.data;
in
{
  domain-media-obsidian-headless-npm-install-is-time-bounded =
    mkEvalCheck "domain-media-obsidian-headless-npm-install-is-time-bounded"
      (lib.hasInfix "/bin/timeout " obsidianHeadlessNpmInstallActivation)
      "The obsidian-headless npm install must run under a timeout. It reaches the public registry and then compiles native modules through node-gyp, and a node-gyp build has no internal bound at all, so an activation step that never returns wedges the whole switch with the new home generation already linked and the system profile still on the old one";

  domain-media-obsidian-headless-npm-install-tolerates-its-own-failure =
    mkEvalCheck "domain-media-obsidian-headless-npm-install-tolerates-its-own-failure"
      (lib.hasInfix "|| true" obsidianHeadlessNpmInstallActivation)
      "The obsidian-headless npm install must end in `|| true`, because home-manager runs activation under set -e and install-obsidian-headless.sh runs under set -euo pipefail, so an offline rebuild, a registry outage or a failed native build aborts the entire switch rather than skipping an optional sync tool";
}
