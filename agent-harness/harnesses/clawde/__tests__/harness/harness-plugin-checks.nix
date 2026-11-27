{
  pkgs,
  mkEvalCheck,
  helpers,
  self,
  cfgWithBothHarnesses,
}:
let
  cfgWithClaudeAgents = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    {
      clawde.agents = {
        agent-with-interactive-settings = {
          harness = "claude";
          personality = "Claude agent carrying interactive settings";
          heartbeatPrompt = "Heartbeat tick.";
          model = "sonnet";
          permissionMode = "bypassPermissions";
          claudeInteractiveSessionSettings = true;
        };
        agent-with-default-settings = {
          harness = "claude";
          personality = "Claude agent carrying default settings";
          heartbeatPrompt = "Heartbeat tick.";
          model = "sonnet";
          permissionMode = "bypassPermissions";
        };
      };
    }
  ];

  claudeCommandsOf =
    agentName:
    let
      inherit (cfgWithClaudeAgents.clawde.harnesses) claude;
      commandArguments = {
        name = agentName;
        agent = cfgWithClaudeAgents.clawde.agents.${agentName};
        workspaceDirectory = "/tmp/${agentName}";
        instructionsFile = "/tmp/${agentName}/instructions.md";
        sessionArgvShellExpansion = "\${CLAWDE_SESSION_ARGV:-}";
        channelLaunchFlags = "";
      };
    in
    [
      (claude.buildLaunchCommandFor commandArguments)
      (claude.buildRunOnceCommandFor commandArguments)
      (claude.buildOneShotTurnCommandFor commandArguments)
    ];

  settingsFilePathIn =
    harnessCommand:
    builtins.elemAt (builtins.match ".* command claude (--plugin-dir [^ ]+ )?--settings ([^ ]+) .*" (builtins.unsafeDiscardStringContext harnessCommand)) 1;

  everyClaudeCommandCarriesTheAgentSettingsFile =
    agentName:
    builtins.all (
      harnessCommand:
      pkgs.lib.hasSuffix "-clawde-agent-${agentName}-claude-settings.json" (
        settingsFilePathIn harnessCommand
      )
    ) (claudeCommandsOf agentName);

  inherit (cfgWithClaudeAgents.claude) interactiveSessionSettings;

  launchSettingsOf = agentName: cfgWithClaudeAgents.clawde.agents.${agentName}.claudeLaunchSettings;
in
{
  clawde-interactive-agent-receives-interactive-settings =
    mkEvalCheck "clawde-interactive-agent-receives-interactive-settings"
      (
        interactiveSessionSettings.pluginConfigs != { }
        && builtins.all (pkgs.lib.hasInfix "--plugin-dir ${builtins.unsafeDiscardStringContext cfgWithClaudeAgents.claude.interactiveSessionModsDirectory} ") (
          claudeCommandsOf "agent-with-interactive-settings"
        )
        && launchSettingsOf "agent-with-interactive-settings" == interactiveSessionSettings
        && everyClaudeCommandCarriesTheAgentSettingsFile "agent-with-interactive-settings"
      )
      "an agent asking for the interactive settings must launch with the same plugins and plugin options the plain claude command gives a keyboard session";

  clawde-default-agent-launches-with-native-settings =
    mkEvalCheck "clawde-default-agent-launches-with-native-settings"
      (
        launchSettingsOf "agent-with-default-settings" == { }
        && builtins.all (harnessCommand: !(pkgs.lib.hasInfix "--settings" harnessCommand)) (
          claudeCommandsOf "agent-with-default-settings"
        )
      )
      "An agent using default settings should launch Claude with its native user settings and without the interactive overlay.";

  clawde-machine-tier-registers-the-complete-plugin =
    mkEvalCheck "clawde-machine-tier-registers-the-complete-plugin"
      (
        toString cfgWithBothHarnesses.home.file.".local/share/agent-plugins/dotfiles".source
        == toString cfgWithBothHarnesses.agentPlugins.bundle
        && pkgs.lib.hasInfix "plugin install dotfiles@dotagents" cfgWithBothHarnesses.home.activation.installProductionClaudePlugin.data
        && !(builtins.hasAttr ".claude/skills/research" cfgWithBothHarnesses.home.file)
      )
      "Claude agents must receive the complete registered production plugin through the shared user profile without a duplicate global research skill projection";

  clawde-steward-payload-is-not-in-the-machine-tier =
    mkEvalCheck "clawde-steward-payload-is-not-in-the-machine-tier"
      (!(builtins.hasAttr ".claude/skills/steward" cfgWithBothHarnesses.home.file))
      "the privileged steward payload must not sit in the machine tier every session loads; it belongs to the steward agent type and is scoped to the steward instance";
}
// import ./harness-interactive-marker-checks.nix {
  inherit
    pkgs
    mkEvalCheck
    cfgWithBothHarnesses
    cfgWithClaudeAgents
    claudeCommandsOf
    ;
}
