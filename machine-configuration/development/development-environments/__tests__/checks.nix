{
  helpers,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  configuration = helpers.homeManagerTestConfiguration [ ../devenv-home-manager.nix ];
  packageNames = map (
    package: package.name or package.pname or "unknown"
  ) configuration.home.packages;
  hasPackageMatching = pattern: builtins.any (name: builtins.match pattern name != null) packageNames;
in
{
  domain-dev-devenv-package =
    mkEvalCheck "domain-dev-devenv-package" (hasPackageMatching ".*devenv.*")
      "devenv package should be installed";
}
