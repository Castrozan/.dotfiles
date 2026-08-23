{
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fixtures = import ./harness-check-fixtures.nix { inherit helpers self; };
  inherit (fixtures) parseDeployedJson;

  cfgWithADeniedAgent = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    {
      clawdeAgentsDeniedDestructiveCommands = [ "denied-agent" ];
      clawde.agents = {
        denied-agent = {
          harness = "claude";
          personality = "Discord agent reachable by strangers";
          channel.type = "discord";
        };
      };
    }
  ];

  cfgWithoutADeniedAgent = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    { clawde.agents.trusted-agent.personality = "agent that keeps its shell"; }
  ];

  deniedAgentsOf =
    configuration:
    parseDeployedJson configuration.home.file."clawde/agents-denied-destructive-commands.json".text;
in
{
  clawde-an-agent-denied-destructive-commands-reaches-the-pre-tool-use-guard =
    mkEvalCheck "clawde-an-agent-denied-destructive-commands-reaches-the-pre-tool-use-guard"
      (deniedAgentsOf cfgWithADeniedAgent == [ "denied-agent" ])
      "codex cannot enforce a call-time permissions.deny entry, so an agent moved onto it silently loses every Bash deny its claude configuration carried; the pre-tool-use guard reads this deployed list to restore that enforcement, and an empty or missing file leaves a Discord-reachable agent with unrestricted shell while the nix option still reads as set";

  clawde-no-agent-is-denied-destructive-commands-by-default =
    mkEvalCheck "clawde-no-agent-is-denied-destructive-commands-by-default"
      (deniedAgentsOf cfgWithoutADeniedAgent == [ ])
      "the denial is opt-in per agent: a steward whose whole job is rebuilding and committing needs rm and sudo, so this must never widen from the listed agents to every clawde agent on the fleet";
}
