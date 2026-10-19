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
in
{
  clawde-workspace-profile-agent-launches-claude-with-the-profile-settings =
    mkEvalCheck "clawde-workspace-profile-agent-launches-claude-with-the-profile-settings"
      (builtins.all (
        harnessCommand:
        pkgs.lib.hasSuffix "-claude-workspace-profile-test-profile-settings.json" (
          settingsFilePathIn harnessCommand
        )
      ) (claudeCommandsOf "agent-with-workspace-profile"))
      "clawde runs the unwrapped claude binary, so an agent never resolves a workspace profile by itself; the launch, run-once and channel turn commands must each hand claude the named profile's settings overlay, or the agent silently runs without the profile's plugins";

  clawde-agent-without-workspace-profile-launches-claude-without-settings =
    mkEvalCheck "clawde-agent-without-workspace-profile-launches-claude-without-settings"
      (builtins.all (harnessCommand: !(pkgs.lib.hasInfix "--settings" harnessCommand)) (
        claudeCommandsOf "agent-without-workspace-profile"
      ))
      "an agent naming no workspace profile must keep the plain launch, so the profile plugins reach only the agents that opted into them";

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
