{
  pkgs,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fixtures = import ../harness-check-fixtures.nix { inherit helpers self; };
  configurations = pkgs.lib.genAttrs [ "rin" "kira" "chise" ] (
    hostname:
    helpers.homeManagerTestConfigurationForLinuxHost hostname (
      fixtures.bothHarnessModules
      ++ [ ../../agents/steward.nix ]
      ++ pkgs.lib.optional (hostname == "kira") {
        clawde.agents.steward = {
          harness = pkgs.lib.mkForce "claude";
          modelByHarness.claude = pkgs.lib.mkForce "claude-sonnet-5-5";
          harnessFallbackChain = pkgs.lib.mkForce [
            "codex"
            "opencode"
          ];
        };
      }
    )
  );
  rinSteward = configurations.rin.clawde.agents.steward;
  kiraSteward = configurations.kira.clawde.agents.steward;
  chiseSteward = configurations.chise.clawde.agents.steward;
  commandBuilders = [
    "buildLaunchCommandFor"
    "buildRunOnceCommandFor"
    "buildOneShotTurnCommandFor"
  ];
  commandAllowedFor =
    hostname: agentName: harnessName: builderName:
    let
      configuration = configurations.${hostname};
      builder = configuration.clawde.harnesses.${harnessName}.${builderName};
    in
    builder == null
    || (
      let
        command = builder {
          name = agentName;
          agent = configuration.clawde.agents.steward // {
            model = "sonnet";
            permissionMode = "default";
            heartbeatPrompt = "Check the harness policy.";
          };
          workspaceDirectory = "/tmp/steward-policy";
          instructionsFile = "/tmp/steward-policy/instructions.md";
          sessionArgvShellExpansion = "\${CLAWDE_SESSION_ARGV:-}";
          channelLaunchFlags = "";
        };
        blocked = hostname == "rin" && agentName == "steward" && harnessName == "claude";
      in
      (command == "${pkgs.coreutils}/bin/false") == blocked
    );
in
{
  clawde-rin-steward-uses-only-codex-and-opencode =
    mkEvalCheck "clawde-rin-steward-uses-only-codex-and-opencode"
      (
        rinSteward.harness == "codex"
        && rinSteward.harnessFallbackChain == [ "opencode" ]
        &&
          builtins.attrNames rinSteward.modelByHarness == [
            "codex"
            "opencode"
          ]
      )
      "Rin's steward defaults to Codex and can fail over only to OpenCode";

  clawde-other-hosts-retain-their-steward-routing =
    mkEvalCheck "clawde-other-hosts-retain-their-steward-routing"
      (
        kiraSteward.harness == "claude"
        && kiraSteward.modelByHarness.claude == "claude-sonnet-5-5"
        &&
          kiraSteward.harnessFallbackChain == [
            "codex"
            "opencode"
          ]
        && chiseSteward.harness == "claude"
        &&
          chiseSteward.harnessFallbackChain == [
            "codex"
            "opencode"
          ]
      )
      "Kira's forced Claude steward and other hosts' shared routing remain valid";

  clawde-steward-launch-policy-is-scoped-to-rin =
    mkEvalCheck "clawde-steward-launch-policy-is-scoped-to-rin"
      (builtins.all
        (
          hostname:
          builtins.all
            (
              agentName:
              builtins.all
                (harnessName: builtins.all (commandAllowedFor hostname agentName harnessName) commandBuilders)
                [
                  "claude"
                  "codex"
                  "opencode"
                ]
            )
            [
              "steward"
              "other-agent"
            ]
        )
        [
          "rin"
          "kira"
          "chise"
        ]
      )
      "every launch mode blocks only Rin's Claude steward, allowing OpenCode and preserving other hosts and agents";
}
