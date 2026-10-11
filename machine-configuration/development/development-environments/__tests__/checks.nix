{
  helpers,
  pkgs,
  lib,
  inputs,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  configuration = helpers.homeManagerTestConfiguration [ ../devenv-home-manager.nix ];
  packageNames = map (
    package: package.name or package.pname or "unknown"
  ) configuration.home.packages;
  hasPackageMatching = pattern: builtins.any (name: builtins.match pattern name != null) packageNames;
  cachedPackage = import ../devenv-cached-package.nix { inherit pkgs inputs; };
  changedSourcePackage = import ../devenv-cached-package.nix {
    inherit pkgs;
    inputs = inputs // {
      devenv.narHash = "sha256-unexpected-source";
    };
  };
in
{
  domain-dev-devenv-package =
    mkEvalCheck "domain-dev-devenv-package" (hasPackageMatching ".*devenv.*")
      "devenv package should be installed";
}
// lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
  domain-dev-devenv-cache-source-guard = mkEvalCheck "domain-dev-devenv-cache-source-guard" (
    !(builtins.tryEval changedSourcePackage.binaryCache).success
  ) "A changed Devenv input must reject stale cached binary metadata";

  domain-dev-devenv-cache-preserves-binary =
    pkgs.runCommand "check-devenv-cache-preserves-binary" { }
      ''
        cmp ${cachedPackage}/bin/devenv ${cachedPackage.binaryCache.storePath}/bin/devenv
        test "$(${cachedPackage}/bin/devenv version)" = "$(${cachedPackage.binaryCache.storePath}/bin/devenv version)"
        touch "$out"
      '';
}
