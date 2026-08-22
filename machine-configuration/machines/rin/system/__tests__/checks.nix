{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  rinHomeManagerConfiguration = helpers.homeManagerTestConfigurationForDarwinHost "rin" [
    ../../../../../agent-harness/harnesses/opencode/opencode.nix
  ];
  rinPackageNames = map (
    package: package.name or package.pname or "unknown"
  ) rinHomeManagerConfiguration.home.packages;
  rinHasPackageMatching =
    pattern: builtins.any (name: builtins.match pattern name != null) rinPackageNames;
in
{
  rin-opencode-package =
    mkEvalCheck "rin-opencode-package" (rinHasPackageMatching ".*opencode.*")
      "Rin must install opencode";

  rin-opencode-bin-wrapper =
    mkEvalCheck "rin-opencode-bin-wrapper"
      (builtins.hasAttr ".local/bin/opencode" rinHomeManagerConfiguration.home.file)
      "Rin must deploy the opencode executable";

}
