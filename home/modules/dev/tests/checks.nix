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
    ../lazygit.nix
    ../devenv.nix
    ../ccost.nix
    ../mcporter.nix
    ../google-workspace-cli.nix
  ];

  packageNames = map (p: p.name or p.pname or "unknown") cfg.home.packages;
  hasPackageMatching = pattern: builtins.any (n: builtins.match pattern n != null) packageNames;
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

  domain-dev-google-cloud-sdk-package =
    mkEvalCheck "domain-dev-google-cloud-sdk-package" (hasPackageMatching ".*google-cloud-sdk.*")
      "google cloud sdk should be installed for google workspace cli setup";
}
