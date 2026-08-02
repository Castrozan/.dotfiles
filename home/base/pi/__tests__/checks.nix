{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  packageNames = map (p: p.name or p.pname or "unknown") cfg.home.packages;
  hasPackageMatching = pattern: builtins.any (n: builtins.match pattern n != null) packageNames;
in
{
  domain-pi-package =
    mkEvalCheck "domain-pi-package" (hasPackageMatching "pi")
      "the pi coding agent should be installed on every machine this repo configures";

  domain-pi-bin-wrapper =
    mkEvalCheck "domain-pi-bin-wrapper" (builtins.hasAttr ".local/bin/pi" cfg.home.file)
      ".local/bin/pi should be in home.file, matching how every other agent harness here is reachable by an absolute path";

  domain-pi-installed-package-is-the-wrapper =
    mkEvalCheck "domain-pi-installed-package-is-the-wrapper" (cfg.pi.package.name == "pi")
      "the upstream release unpacks to a directory of sidecar assets around a Bun executable and carries no bin/, so installing it raw would put nothing on PATH. Only the wrapper exposes a `pi` binary";
}
