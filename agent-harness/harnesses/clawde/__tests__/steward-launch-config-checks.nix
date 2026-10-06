{
  pkgs,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fixtures = import ./harness-check-fixtures.nix { inherit helpers self; };
  inherit (fixtures) bothHarnessModules cfgWithBothHarnesses parseDeployedJson;

  launchArgumentsForEffort = reasoningEffort: {
    name = "effort-check";
    agent = cfgWithBothHarnesses.clawde.agents.agent-on-claude // {
      inherit reasoningEffort;
      model = "sonnet";
      permissionMode = "default";
      heartbeatPrompt = "Check the effort setting.";
    };
    workspaceDirectory = "/tmp/effort-check";
    instructionsFile = "/tmp/effort-check/instructions.md";
    sessionArgvShellExpansion = "\${CLAWDE_SESSION_ARGV:-}";
    channelLaunchFlags = "";
  };

  commandBuilders = [
    "buildLaunchCommandFor"
    "buildRunOnceCommandFor"
    "buildOneShotTurnCommandFor"
  ];

  stewardLaunchConfig =
    parseDeployedJson
      (helpers.homeManagerTestConfiguration (bothHarnessModules ++ [ ../agents/steward.nix ]))
      .home.file."clawde/launch-config/steward.json".text;

  stewardPersonalityForHost =
    hostname:
    (helpers.homeManagerTestConfigurationForLinuxHost hostname (
      bothHarnessModules ++ [ ../agents/steward.nix ]
    )).clawde.agents.steward.personality;

  rinStewardLaunchConfig =
    parseDeployedJson
      (helpers.homeManagerTestConfigurationForLinuxHost "rin" (
        bothHarnessModules ++ [ ../agents/steward.nix ]
      )).home.file."clawde/launch-config/steward.json".text;
in
{
  clawde-rin-steward-checks-activation-before-its-model-gate =
    mkEvalCheck "clawde-rin-steward-checks-activation-before-its-model-gate"
      (builtins.any (
        argument:
        builtins.isString argument
        && builtins.match ".*steward-rebuild.*clawde-heartbeat-change-gate.*" argument != null
      ) rinStewardLaunchConfig.heartbeat_driver_argv)
      "a dirty or unreachable upstream must not suppress local activation when the heartbeat suppresses repeated model turns";

  clawde-steward-standing-activation-permission-is-scoped-to-rin =
    mkEvalCheck "clawde-steward-standing-activation-permission-is-scoped-to-rin"
      (
        pkgs.lib.hasInfix "### Standing activation permission" (stewardPersonalityForHost "rin")
        && !(pkgs.lib.hasInfix "### Standing activation permission" (stewardPersonalityForHost "kira"))
        && !(pkgs.lib.hasInfix "### Standing activation permission" (stewardPersonalityForHost "chise"))
      )
      "rin's standing operator approval must reach its steward without authorizing activation during active use on other hosts";

  clawde-claude-effort-reaches-every-launch-mode =
    mkEvalCheck "clawde-claude-effort-reaches-every-launch-mode"
      (builtins.all
        (
          reasoningEffort:
          builtins.all (
            builderName:
            pkgs.lib.hasPrefix "CLAUDE_CODE_EFFORT_LEVEL=${reasoningEffort} " (
              cfgWithBothHarnesses.clawde.harnesses.claude.${builderName} (
                launchArgumentsForEffort reasoningEffort
              )
            )
          ) commandBuilders
        )
        [
          "low"
          "high"
        ]
      )
      "Claude interactive, scheduled, and channel launches must receive the agent's explicit effort instead of inheriting the model or user's saved default";

  clawde-claude-effort-does-not-change-other-harness-launches =
    mkEvalCheck "clawde-claude-effort-does-not-change-other-harness-launches"
      (builtins.all
        (
          harnessName:
          builtins.all (
            builderName:
            !(pkgs.lib.hasInfix "CLAUDE_CODE_EFFORT_LEVEL" (
              cfgWithBothHarnesses.clawde.harnesses.${harnessName}.${builderName} (
                launchArgumentsForEffort "high"
              )
            ))
          ) commandBuilders
        )
        [
          "codex"
          "opencode"
        ]
      )
      "Claude's effort environment belongs only to Claude; Codex and OpenCode keep their native configuration paths";

  clawde-the-heartbeat-driver-carries-its-own-module-search-path =
    mkEvalCheck "clawde-the-heartbeat-driver-carries-its-own-module-search-path"
      (builtins.any (
        argument: pkgs.lib.hasPrefix "PYTHONPATH=" argument
      ) stewardLaunchConfig.heartbeat_driver_argv)
      "a rebuild regenerates this argv with the new generation's driver script while the supervisor that spawns it keeps the PYTHONPATH it launched with, so a driver relying on the inherited one dies on ModuleNotFoundError the moment a running agent restarts its session, and the watchdog then restart-loops the agent on a widening backoff until the whole supervisor is respawned";

  clawde-the-steward-can-fall-off-a-harness-that-stops-producing-turns =
    mkEvalCheck "clawde-the-steward-can-fall-off-a-harness-that-stops-producing-turns"
      (
        builtins.filter (
          harnessName: harnessName != stewardLaunchConfig.declared_harness
        ) stewardLaunchConfig.harness_fallback_chain != [ ]
      )
      "the steward is the one agent nothing else watches, so a fallback chain holding nothing but its own declared harness leaves it parked and silent the next time its provider refuses work: it holds a live process, an idle pane and a firing heartbeat throughout, which is how it once sat out three days of a weekly usage limit while every liveness probe reported it healthy";

  clawde-every-steward-fallback-is-a-harness-it-can-actually-reach =
    mkEvalCheck "clawde-every-steward-fallback-is-a-harness-it-can-actually-reach"
      (builtins.all (
        harnessName:
        builtins.elem harnessName (builtins.attrNames stewardLaunchConfig.harness_launch_commands)
      ) stewardLaunchConfig.harness_fallback_chain)
      "the runtime skips a fallback the agent is not eligible for, so a chain naming a harness this machine never materialized a launch command for silently shortens to nothing and the failover reads as configured while doing nothing";
}
