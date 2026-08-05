{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../lazygit.nix
    ../devenv.nix
    ../ccost.nix
    ../ccusage.nix
    ../mcporter.nix
    ../google-workspace-cli
  ];

  mcporterNpmInstallActivation = cfg.home.activation.installMcporterViaNpm.data;

  packageNames = map (p: p.name or p.pname or "unknown") cfg.home.packages;
  hasPackageMatching = pattern: builtins.any (n: builtins.match pattern n != null) packageNames;

  darwinCfg = helpers.homeManagerTestConfigurationForDarwin [
    ../ccost.nix
    ../ccusage.nix
  ];
  darwinPackageNames = map (p: p.name or p.pname or "unknown") darwinCfg.home.packages;
  darwinHasPackageMatching =
    pattern: builtins.any (n: builtins.match pattern n != null) darwinPackageNames;
in
{
  domain-dev-lazygit-enabled =
    mkEvalCheck "domain-dev-lazygit-enabled" cfg.programs.lazygit.enable
      "lazygit should be enabled";

  domain-dev-devenv-package =
    mkEvalCheck "domain-dev-devenv-package" (hasPackageMatching ".*devenv.*")
      "devenv package should be installed";

  domain-dev-google-workspace-cli-package =
    mkEvalCheck "domain-dev-google-workspace-cli-package"
      (hasPackageMatching ".*google-workspace-cli-auth-login-with-chrome-global.*")
      "google workspace cli auth helper should be installed";

  domain-dev-google-chat-browser-cli-package =
    mkEvalCheck "domain-dev-google-chat-browser-cli-package"
      (hasPackageMatching ".*google-chat-browser-cli.*")
      "google chat browser cli should be installed as the non-GCP fallback";

  domain-dev-google-cloud-sdk-package =
    mkEvalCheck "domain-dev-google-cloud-sdk-package" (hasPackageMatching ".*google-cloud-sdk.*")
      "google cloud sdk should be installed for google workspace cli setup";

  domain-dev-ccost-package-linux =
    mkEvalCheck "domain-dev-ccost-package-linux" (hasPackageMatching ".*ccost.*")
      "ccost cost tracker should resolve to a package on linux";

  domain-dev-ccost-package-darwin =
    mkEvalCheck "domain-dev-ccost-package-darwin" (darwinHasPackageMatching ".*ccost.*")
      "ccost must select a darwin prebuilt binary so it installs on darwin, not only linux";

  domain-dev-ccusage-package-linux =
    mkEvalCheck "domain-dev-ccusage-package-linux" (hasPackageMatching ".*ccusage.*")
      "ccusage usage tracker should resolve to a package on linux";

  domain-dev-ccusage-package-darwin =
    mkEvalCheck "domain-dev-ccusage-package-darwin" (darwinHasPackageMatching ".*ccusage.*")
      "ccusage must select a darwin prebuilt binary so it installs on darwin, not only linux";

  domain-dev-mcporter-npm-install-is-time-bounded =
    mkEvalCheck "domain-dev-mcporter-npm-install-is-time-bounded"
      (lib.hasInfix "/bin/timeout " mcporterNpmInstallActivation)
      "The mcporter npm install must run under a timeout, because it reaches the public registry and then runs package lifecycle scripts, neither of which the activation can bound on its own, and an activation step that never returns wedges the whole switch with the new home generation already linked and the system profile still on the old one";

  domain-dev-mcporter-npm-install-tolerates-its-own-failure =
    mkEvalCheck "domain-dev-mcporter-npm-install-tolerates-its-own-failure"
      (lib.hasInfix "|| true" mcporterNpmInstallActivation)
      "The mcporter npm install must end in `|| true`, because home-manager runs activation under set -e and the install script itself runs under set -euo pipefail, so any registry outage, offline rebuild or failed lifecycle script aborts the entire switch; installing a convenience CLI is best-effort and must never be able to fail a rebuild";
}
