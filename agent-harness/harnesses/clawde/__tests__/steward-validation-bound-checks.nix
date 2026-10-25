{
  pkgs,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fixtures = import ./harness-check-fixtures.nix { inherit helpers self; };

  stewardHomeConfiguration = helpers.homeManagerTestConfigurationForLinuxHost "chise" (
    fixtures.bothHarnessModules ++ [ ../agents/steward.nix ]
  );

  validationScopeDropin =
    stewardHomeConfiguration.xdg.configFile."systemd/user/steward-validate-.scope.d/background-steward.conf".text;

  validationSlice = stewardHomeConfiguration.systemd.user.slices.background-steward;
in
{
  clawde-steward-validations-run-in-a-memory-bounded-background-slice =
    mkEvalCheck "clawde-steward-validations-run-in-a-memory-bounded-background-slice"
      (
        pkgs.lib.hasInfix "Slice=background-steward.slice" validationScopeDropin
        && (validationSlice.Slice.MemoryHigh or null) != null
      )
      "every steward-validate-<revision>.scope must land in background-steward.slice, a child of the standard background.slice carrying a MemoryHigh bound, so a revision validation reclaims its own evaluator pages instead of the interactive desktop's";
}
