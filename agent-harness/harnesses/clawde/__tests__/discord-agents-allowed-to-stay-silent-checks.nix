{
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fixtures = import ./harness-check-fixtures.nix { inherit helpers self; };
  inherit (fixtures) parseDeployedJson;

  cfgWithASilentDiscordAgent = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    {
      clawdeDiscordAgentsAllowedToStaySilent = [ "quiet-agent" ];
      clawde.agents = {
        quiet-agent = {
          harness = "claude";
          personality = "Discord agent that answers only when addressed";
          channel.type = "discord";
        };
        answering-agent = {
          harness = "claude";
          personality = "Discord agent that answers everything";
          channel.type = "discord";
        };
      };
    }
  ];

  workspaceSettingsOfAgent =
    agentName:
    parseDeployedJson
      cfgWithASilentDiscordAgent.home.file."clawde/${agentName}/.claude/settings.json".text;
in
{
  clawde-a-discord-agent-allowed-to-stay-silent-runs-with-hooks-off =
    mkEvalCheck "clawde-a-discord-agent-allowed-to-stay-silent-runs-with-hooks-off"
      ((workspaceSettingsOfAgent "quiet-agent").disableAllHooks or false)
      "the discord channel adapter blocks any turn that ends without a call to the reply tool, so an agent whose whole design is choosing when to speak answers every message it meant to ignore with a placeholder; disableAllHooks in its own workspace settings is what lets the turn end silently";

  clawde-a-discord-agent-not-listed-keeps-its-reply-enforcement =
    mkEvalCheck "clawde-a-discord-agent-not-listed-keeps-its-reply-enforcement"
      (
        !((workspaceSettingsOfAgent "answering-agent") ? disableAllHooks)
        && (workspaceSettingsOfAgent "answering-agent") ? hooks
      )
      "silence is opt-in per agent: an assistant agent that answers its owner still needs the Stop hook that catches an answer left in the terminal, so this must never widen from the listed agents to every discord agent on the fleet";

  clawde-a-silent-discord-agent-keeps-the-channel-plugin-enabled =
    mkEvalCheck "clawde-a-silent-discord-agent-keeps-the-channel-plugin-enabled"
      ((workspaceSettingsOfAgent "quiet-agent").enabledPlugins."discord@claude-plugins-official" or false)
      "the silence opt-in adds one setting beside what the channel adapter writes rather than replacing it; losing the plugin entry here takes the agent off Discord entirely, which reads exactly like a bot that went quiet on purpose";
}
