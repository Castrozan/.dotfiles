{
  pkgs,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fixtures = import ./harness-check-fixtures.nix { inherit helpers self; };

  stewardHomeConfigurationForHost =
    hostname:
    helpers.homeManagerTestConfigurationForLinuxHost hostname (
      fixtures.bothHarnessModules ++ [ ../agents/steward.nix ]
    );

  chiseStewardHome = stewardHomeConfigurationForHost "chise";

  boundedScopeDropinForPrefix =
    prefix:
    chiseStewardHome.xdg.configFile."systemd/user/${prefix}-.scope.d/background-steward.conf".text;

  validationSlice = chiseStewardHome.systemd.user.slices.background-steward;

  launchConfigForHost =
    hostname:
    fixtures.parseDeployedJson
      (stewardHomeConfigurationForHost hostname).home.file."clawde/launch-config/steward.json".text;

  chiseLaunchConfig = launchConfigForHost "chise";
in
{
  clawde-steward-validations-run-in-a-memory-bounded-background-slice =
    mkEvalCheck "clawde-steward-validations-run-in-a-memory-bounded-background-slice"
      (
        builtins.all
          (prefix: pkgs.lib.hasInfix "Slice=background-steward.slice" (boundedScopeDropinForPrefix prefix))
          [
            "steward-validate"
            "steward-activation"
          ]
        && (validationSlice.Slice.MemoryHigh or null) != null
      )
      "every steward-validate-<revision>.scope and steward-activation-<revision>.scope must land in background-steward.slice, a child of the standard background.slice carrying a MemoryHigh bound, so a steward build reclaims its own evaluator pages instead of the interactive desktop's";

  clawde-chise-steward-wakes-its-model-only-for-a-cycle-failure =
    mkEvalCheck "clawde-chise-steward-wakes-its-model-only-for-a-cycle-failure"
      (
        chiseLaunchConfig.launch_gate_interval_seconds == 300
        &&
          builtins.match ".*steward-cycle run.*clawde-heartbeat-change-gate.*steward-cycle attention.*" (
            builtins.replaceStrings [ "\n" ] [ " " ] chiseLaunchConfig.launch_gate_command
          ) != null
        && chiseStewardHome.systemd.user.services ? steward-operator-idle-marker
        && pkgs.lib.hasInfix "### Chise maintenance cycle" chiseStewardHome.clawde.agents.steward.personality
      )
      "chise's steward must keep no warm model session: the deterministic cycle runs on the launch gate, and only the failure it records in attention.json may launch a model turn";

  clawde-steward-maintenance-cycle-is-scoped-to-chise =
    mkEvalCheck "clawde-steward-maintenance-cycle-is-scoped-to-chise"
      (builtins.all
        (
          hostname:
          let
            home = stewardHomeConfigurationForHost hostname;
          in
          (launchConfigForHost hostname).launch_gate_command or null == null
          && !(home.systemd.user.services ? steward-operator-idle-marker)
          && !(pkgs.lib.hasInfix "### Chise maintenance cycle" home.clawde.agents.steward.personality)
        )
        [
          "kira"
          "rin"
        ]
      )
      "the maintenance cycle validates and activates through chise's machine-local entrypoint, so another host must keep its own steward loop";
}
