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

  stewardHomeConfiguration = helpers.homeManagerTestConfiguration (
    bothHarnessModules ++ [ ../agents/steward.nix ]
  );

  stewardLaunchConfig =
    parseDeployedJson
      stewardHomeConfiguration.home.file."clawde/launch-config/steward.json".text;

  heartbeatDrivenLaunchConfig =
    parseDeployedJson
      (helpers.homeManagerTestConfiguration (
        bothHarnessModules
        ++ [
          {
            clawde.agents.heartbeat-driven-agent = {
              harness = "claude";
              personality = "Heartbeat driven agent";
              heartbeatInterval = "*/30 * * * *";
              heartbeatPrompt = "Check in.";
            };
          }
        ]
      )).home.file."clawde/launch-config/heartbeat-driven-agent.json".text;

  codexCommandForHost =
    hostname: agentName: commandBuilderName:
    (helpers.homeManagerTestConfigurationForLinuxHost hostname bothHarnessModules)
    .clawde.harnesses.codex.${commandBuilderName}
      ((launchArgumentsForEffort "high") // { name = agentName; });
in
{
  clawde-rin-steward-restores-terminal-space-before-interactive-launch =
    mkEvalCheck "clawde-rin-steward-restores-terminal-space-before-interactive-launch"
      (pkgs.lib.hasInfix "steward_terminal_space.py &&" (
        codexCommandForHost "rin" "steward" "buildLaunchCommandFor"
      ))
      "Rin's collapsed steward pane must regain drawable terminal space before Codex resumes";

  clawde-steward-terminal-space-guard-is-scoped =
    mkEvalCheck "clawde-steward-terminal-space-guard-is-scoped"
      (builtins.all (command: !(pkgs.lib.hasInfix "steward_terminal_space.py" command)) [
        (codexCommandForHost "kira" "steward" "buildLaunchCommandFor")
        (codexCommandForHost "chise" "steward" "buildLaunchCommandFor")
        (codexCommandForHost "rin" "other-agent" "buildLaunchCommandFor")
        (codexCommandForHost "rin" "steward" "buildRunOnceCommandFor")
        (codexCommandForHost "rin" "steward" "buildOneShotTurnCommandFor")
      ])
      "the terminal repair belongs only to Rin's interactive steward launch";

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

  clawde-the-steward-launch-gate-carries-its-own-module-search-path =
    mkEvalCheck "clawde-the-steward-launch-gate-carries-its-own-module-search-path"
      (
        stewardLaunchConfig.heartbeat_driver_argv == null
        && pkgs.lib.hasInfix "-steward-cycle/bin/steward-cycle run" stewardLaunchConfig.launch_gate_command
      )
      "the launch gate replaces the heartbeat driver and runs inside a supervisor that keeps the environment it launched with, so it must reach the cycle through the generation's own steward-cycle wrapper instead of any inherited PYTHONPATH, or a rebuild leaves the gate failing on ModuleNotFoundError while the steward never launches";

  clawde-the-heartbeat-driver-carries-its-own-module-search-path =
    mkEvalCheck "clawde-the-heartbeat-driver-carries-its-own-module-search-path"
      (builtins.any (
        argument: pkgs.lib.hasPrefix "PYTHONPATH=" argument
      ) heartbeatDrivenLaunchConfig.heartbeat_driver_argv)
      "a rebuild regenerates this argv with the new generation's driver script while the supervisor that spawns it keeps the PYTHONPATH it launched with, so a driver relying on the inherited one dies on ModuleNotFoundError the moment a running agent restarts its session, and the watchdog then restart-loops the agent on a widening backoff until the whole supervisor is respawned";

  clawde-the-steward-runs-only-on-codex =
    mkEvalCheck "clawde-the-steward-runs-only-on-codex"
      (
        stewardLaunchConfig.declared_harness == "codex"
        && stewardLaunchConfig.harness_fallback_chain == [ ]
        && builtins.attrNames stewardHomeConfiguration.clawde.agents.steward.modelByHarness == [ "codex" ]
        && pkgs.lib.hasInfix "command codex " stewardLaunchConfig.harness_launch_commands.codex
      )
      "the personal steward must use only Codex and must never fall back to a harness that can charge the work account";

  clawde-the-steward-cannot-launch-another-harness =
    mkEvalCheck "clawde-the-steward-cannot-launch-another-harness"
      (builtins.all
        (
          harnessName:
          builtins.all (
            builderName:
            let
              builder = cfgWithBothHarnesses.clawde.harnesses.${harnessName}.${builderName};
            in
            builder == null
            ||
              builder ((launchArgumentsForEffort "high") // { name = "steward"; })
              == "${pkgs.coreutils}/bin/false"
          ) commandBuilders
        )
        (
          builtins.filter (harnessName: harnessName != "codex") (
            builtins.attrNames cfgWithBothHarnesses.clawde.harnesses
          )
        )
      )
      "manual switches and stale runtime overrides must fail before starting a non-Codex steward in every launch mode";

  clawde-every-steward-fallback-is-a-harness-it-can-actually-reach =
    mkEvalCheck "clawde-every-steward-fallback-is-a-harness-it-can-actually-reach"
      (builtins.all (
        harnessName:
        builtins.elem harnessName (builtins.attrNames stewardLaunchConfig.harness_launch_commands)
      ) stewardLaunchConfig.harness_fallback_chain)
      "the runtime skips a fallback the agent is not eligible for, so a chain naming a harness this machine never materialized a launch command for silently shortens to nothing and the failover reads as configured while doing nothing";
}
