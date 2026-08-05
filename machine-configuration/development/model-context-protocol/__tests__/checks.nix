{
  helpers,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  configuration = helpers.homeManagerTestConfiguration [ ../mcporter-home-manager.nix ];
  mcporterNpmInstallActivation = configuration.home.activation.installMcporterViaNpm.data;
in
{
  domain-dev-mcporter-npm-install-is-time-bounded =
    mkEvalCheck "domain-dev-mcporter-npm-install-is-time-bounded"
      (lib.hasInfix "/bin/timeout " mcporterNpmInstallActivation)
      "The mcporter npm install must run under a timeout, because it reaches the public registry and then runs package lifecycle scripts, neither of which the activation can bound on its own, and an activation step that never returns wedges the whole switch with the new home generation already linked and the system profile still on the old one";

  domain-dev-mcporter-npm-install-tolerates-its-own-failure =
    mkEvalCheck "domain-dev-mcporter-npm-install-tolerates-its-own-failure"
      (lib.hasInfix "|| true" mcporterNpmInstallActivation)
      "The mcporter npm install must end in `|| true`, because home-manager runs activation under set -e and the install script itself runs under set -euo pipefail, so any registry outage, offline rebuild or failed lifecycle script aborts the entire switch; installing a convenience CLI is best-effort and must never be able to fail a rebuild";
}
