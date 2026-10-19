{
  pkgs,
  mkEvalCheck,
  helpers,
  self,
  cfgWithBothHarnesses,
}:
let
  cfgWithWorkspaceProfileAgent = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    {
      disabledModules = [ ../../../workspace-profiles ];
      options.agentWorkspaceProfiles = pkgs.lib.mkOption {
        type = pkgs.lib.types.attrsOf pkgs.lib.types.anything;
      };
      config.agentWorkspaceProfiles = {
        profiles = [
          {
            name = "test-profile";
            directoryPrefixes = [ ];
            gitRemotePatterns = [ "gitlab.example.invalid" ];
            instructionFiles = [ ];
            claudeCode.settingsOverlay.enabledPlugins."test-profile-plugin@test-marketplace" = true;
            codex = { };
            opencode = { };
          }
        ];
        routingTableFile = "/dev/null";
        resolverExecutable = "/usr/bin/false";
      };
    }
    {
      clawde.agents = {
        agent-with-workspace-profile = {
          harness = "claude";
          personality = "Claude agent carrying a workspace profile";
          heartbeatPrompt = "Heartbeat tick.";
          model = "sonnet";
          permissionMode = "bypassPermissions";
          claudeSettingsWorkspaceProfile = "test-profile";
        };
        agent-with-interactive-settings-and-workspace-profile = {
          harness = "claude";
          personality = "Claude agent carrying interactive settings and a workspace profile";
          heartbeatPrompt = "Heartbeat tick.";
          model = "sonnet";
          permissionMode = "bypassPermissions";
          claudeInteractiveSessionSettings = true;
          claudeSettingsWorkspaceProfile = "test-profile";
        };
        agent-without-workspace-profile = {
          harness = "claude";
          personality = "Claude agent carrying no workspace profile";
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
      inherit (cfgWithWorkspaceProfileAgent.clawde.harnesses) claude;
      commandArguments = {
        name = agentName;
        agent = cfgWithWorkspaceProfileAgent.clawde.agents.${agentName};
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
    builtins.head (
      builtins.match ".* command claude --settings ([^ ]+) .*" (
        builtins.unsafeDiscardStringContext harnessCommand
      )
    );

  everyClaudeCommandCarriesTheAgentSettingsFile =
    agentName:
    builtins.all (
      harnessCommand:
      pkgs.lib.hasSuffix "-clawde-agent-${agentName}-claude-settings.json" (
        settingsFilePathIn harnessCommand
      )
    ) (claudeCommandsOf agentName);

  testProfileSettingsOverlay.enabledPlugins."test-profile-plugin@test-marketplace" = true;

  inherit (cfgWithWorkspaceProfileAgent.claude) interactiveSessionSettings;

  launchSettingsOf = agentName: cfgWithWorkspaceProfileAgent.clawde.agents.${agentName}.claudeLaunchSettings;
in
{
  clawde-workspace-profile-agent-launches-claude-with-the-profile-settings =
    mkEvalCheck "clawde-workspace-profile-agent-launches-claude-with-the-profile-settings"
      (
        launchSettingsOf "agent-with-workspace-profile" == testProfileSettingsOverlay
        && everyClaudeCommandCarriesTheAgentSettingsFile "agent-with-workspace-profile"
      )
      "clawde runs the unwrapped claude binary, so an agent never resolves a workspace profile by itself; the launch, run-once and channel turn commands must each hand claude the named profile's settings overlay, or the agent silently runs without the profile's plugins";

  clawde-interactive-settings-agent-layers-the-profile-over-the-interactive-settings =
    mkEvalCheck "clawde-interactive-settings-agent-layers-the-profile-over-the-interactive-settings"
      (
        interactiveSessionSettings.enabledPlugins != { }
        &&
          launchSettingsOf "agent-with-interactive-settings-and-workspace-profile"
          == pkgs.lib.recursiveUpdate interactiveSessionSettings testProfileSettingsOverlay
        && everyClaudeCommandCarriesTheAgentSettingsFile "agent-with-interactive-settings-and-workspace-profile"
      )
      "an agent asking for the interactive settings must launch with the same plugins and plugin options the plain claude command gives a keyboard session, with the workspace profile overlay winning where they overlap exactly as the interactive wrapper layers them";

  clawde-agent-without-workspace-profile-launches-claude-without-settings =
    mkEvalCheck "clawde-agent-without-workspace-profile-launches-claude-without-settings"
      (
        launchSettingsOf "agent-without-workspace-profile" == { }
        && builtins.all (harnessCommand: !(pkgs.lib.hasInfix "--settings" harnessCommand)) (
          claudeCommandsOf "agent-without-workspace-profile"
        )
      )
      "an agent asking for no launch settings must keep the plain launch, so the interactive and profile plugins reach only the agents that opted into them";

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
