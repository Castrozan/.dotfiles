{
  pkgs,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fixtures = import ./harness-check-fixtures.nix { inherit helpers self; };

  stewardModules = fixtures.bothHarnessModules ++ [ ../agents/steward.nix ];

  stewardHomeConfigurationForHost =
    hostname:
    if hostname == "chise" then
      helpers.homeManagerTestConfigurationForLinuxHost hostname stewardModules
    else
      helpers.homeManagerTestConfigurationForDarwinHost hostname stewardModules;

  chiseStewardHome = stewardHomeConfigurationForHost "chise";

  boundedScopeDropinForPrefix =
    prefix:
    chiseStewardHome.xdg.configFile."systemd/user/${prefix}-.scope.d/background-steward.conf".text;

  validationSlice = chiseStewardHome.systemd.user.slices.background-steward;

  launchConfigForHost =
    hostname:
    fixtures.parseDeployedJson
      (stewardHomeConfigurationForHost hostname).home.file."clawde/launch-config/steward.json".text;

  cycleSettingsForHost =
    hostname:
    builtins.fromJSON (
      builtins.unsafeDiscardStringContext
        (stewardHomeConfigurationForHost hostname).home.file."clawde/steward/cycle-settings.json".text
    );

  fleetHosts = [
    "chise"
    "kira"
    "rin"
  ];
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

  clawde-steward-wakes-its-model-only-for-a-cycle-failure =
    mkEvalCheck "clawde-steward-wakes-its-model-only-for-a-cycle-failure"
      (builtins.all (
        hostname:
        let
          launchConfig = launchConfigForHost hostname;
        in
        launchConfig.launch_gate_interval_seconds == 300
        &&
          builtins.match ".*steward-cycle run.*clawde-heartbeat-change-gate.*steward-cycle attention.*" (
            builtins.replaceStrings [ "\n" ] [ " " ] launchConfig.launch_gate_command
          ) != null
        && pkgs.lib.hasInfix "### Maintenance cycle" (stewardHomeConfigurationForHost hostname)
        .clawde.agents.steward.personality
      ) fleetHosts)
      "every steward must keep no warm model session: the deterministic cycle runs on the launch gate, and only the failure it records in attention.json may launch a model turn";

  clawde-steward-cycle-settings-follow-each-host-platform =
    mkEvalCheck "clawde-steward-cycle-settings-follow-each-host-platform"
      (
        let
          chise = cycleSettingsForHost "chise";
          kira = cycleSettingsForHost "kira";
          rin = cycleSettingsForHost "rin";
        in
        chise.job_isolation == "systemd-scope"
        && chise.entrypoint != null
        && chise.idle_marker_name != null
        && chise.operator_idle_required
        && chiseStewardHome.systemd.user.services ? steward-operator-idle-marker
        && builtins.all (settings: settings.job_isolation == "darwin-background") [
          kira
          rin
        ]
        && builtins.all (settings: settings.entrypoint == null && settings.idle_marker_name == null) [
          kira
          rin
        ]
        && kira.configuration_attribute == "darwinConfigurations.kira.system"
        && kira.operator_idle_required
        && !rin.operator_idle_required
      )
      "chise validates through its machine-local entrypoint inside memory-bounded scopes and waits for the hypridle marker; the macs build the pinned repository at background priority, kira waits for an idle human interface, and rin keeps its standing permission to activate during active use";
}
