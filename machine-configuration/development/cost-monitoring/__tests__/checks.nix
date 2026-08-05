{
  helpers,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  linuxConfiguration = helpers.homeManagerTestConfiguration [
    ../ccost-home-manager.nix
    ../ccusage-home-manager.nix
  ];
  darwinConfiguration = helpers.homeManagerTestConfigurationForDarwin [
    ../ccost-home-manager.nix
    ../ccusage-home-manager.nix
  ];
  packageNames =
    configuration:
    map (package: package.name or package.pname or "unknown") configuration.home.packages;
  hasPackageMatching =
    configuration: pattern:
    builtins.any (name: builtins.match pattern name != null) (packageNames configuration);
in
{
  domain-dev-ccost-package-linux =
    mkEvalCheck "domain-dev-ccost-package-linux" (hasPackageMatching linuxConfiguration ".*ccost.*")
      "ccost cost tracker should resolve to a package on linux";

  domain-dev-ccost-package-darwin =
    mkEvalCheck "domain-dev-ccost-package-darwin" (hasPackageMatching darwinConfiguration ".*ccost.*")
      "ccost must select a darwin prebuilt binary so it installs on darwin, not only linux";

  domain-dev-ccusage-package-linux =
    mkEvalCheck "domain-dev-ccusage-package-linux" (hasPackageMatching linuxConfiguration ".*ccusage.*")
      "ccusage usage tracker should resolve to a package on linux";

  domain-dev-ccusage-package-darwin =
    mkEvalCheck "domain-dev-ccusage-package-darwin"
      (hasPackageMatching darwinConfiguration ".*ccusage.*")
      "ccusage must select a darwin prebuilt binary so it installs on darwin, not only linux";
}
