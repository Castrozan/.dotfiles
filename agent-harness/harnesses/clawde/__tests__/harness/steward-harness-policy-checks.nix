{
  pkgs,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fixtures = import ../harness-check-fixtures.nix { inherit helpers self; };

  stewardWithClaudeOverride = helpers.homeManagerTestConfiguration (
    fixtures.bothHarnessModules
    ++ [
      ../../agents/steward.nix
      {
        clawde.agents.steward = {
          harness = pkgs.lib.mkForce "claude";
          modelByHarness.claude = pkgs.lib.mkForce "claude-sonnet-5-5";
          harnessFallbackChain = pkgs.lib.mkForce [
            "codex"
            "opencode"
          ];
        };
      }
    ]
  );
in
{
  clawde-the-steward-rejects-host-routing-overrides =
    mkEvalCheck "clawde-the-steward-rejects-host-routing-overrides"
      (builtins.any (
        assertion:
        assertion.message
        == "The steward must run only on Codex, without fallback harnesses or non-Codex model overrides."
        && !assertion.assertion
      ) stewardWithClaudeOverride.assertions)
      "a host's forced Claude settings must fail the shared steward assertion before the configuration can deploy";
}
