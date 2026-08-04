{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  packageNames = map (p: p.name or p.pname or "unknown") cfg.home.packages;
  hasPackageMatching = pattern: builtins.any (n: builtins.match pattern n != null) packageNames;
in
{
  domain-sourcebot-package =
    mkEvalCheck "domain-sourcebot-package" (hasPackageMatching ".*sourcebot.*")
      "sourcebot package should be installed";
}
