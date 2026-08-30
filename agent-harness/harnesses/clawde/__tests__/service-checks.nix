{
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  cfgWithClawdeAgent = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    {
      clawde.agents.test-agent = {
        channel.type = "discord";
        channel.discord.botTokenSecretName = "discord-bot-token-test";
        personality = "Test personality";
      };
    }
  ];

  cfgWithClawdeAgentsOnDistinctSessions = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    {
      clawde.agents = {
        agent-on-default-session = {
          channel.type = "discord";
          channel.discord.botTokenSecretName = "discord-bot-token-test";
          personality = "Default session agent personality";
        };
        agent-on-custom-session = {
          channel.type = "discord";
          channel.discord.botTokenSecretName = "discord-bot-token-test";
          tmuxSession = "custom-session-for-this-agent";
          personality = "Custom session agent personality";
        };
      };
    }
  ];

  clawdeService = cfgWithClawdeAgent.systemd.user.services.clawde;
in
{
  clawde-stop-does-not-take-the-fleet-with-it =
    mkEvalCheck "clawde-stop-does-not-take-the-fleet-with-it"
      (
        !(clawdeService.Unit.X-RestartIfChanged or true)
        && (clawdeService.Service.KillMode or null) == "process"
        && !(clawdeService.Service ? ExecStop)
      )
      "clawde.service must stop only the supervisor process, preserve the agent processes it coordinates, and avoid rebuild-driven restart churn";

  clawde-consumes-herdr-without-owning-its-lifecycle =
    mkEvalCheck "clawde-consumes-herdr-without-owning-its-lifecycle"
      (
        builtins.elem "herdr.service" (clawdeService.Unit.Wants or [ ])
        && builtins.elem "herdr.service" (clawdeService.Unit.After or [ ])
        && !(builtins.elem "herdr.service" (clawdeService.Unit.Requires or [ ]))
        && !(clawdeService.Service ? MemoryHigh)
      )
      "clawde.service must attach to the independently managed herdr.service through Wants plus After, never own its lifecycle through Requires or carry the shared server's cgroup memory policy";

  clawde-depends-on-agenix-without-inheriting-its-deactivation =
    mkEvalCheck "clawde-depends-on-agenix-without-inheriting-its-deactivation"
      (
        !(builtins.elem "agenix.service" (clawdeService.Unit.Requires or [ ]))
        && builtins.elem "agenix.service" (clawdeService.Unit.Wants or [ ])
        && builtins.elem "agenix.service" (clawdeService.Unit.After or [ ])
      )
      "clawde.service must reach agenix through Wants plus After and never through Requires. Wants and After together are the whole reason the dependency exists: they get the bot tokens decrypted before the supervisor starts on boot. Requires would add deactivation propagation on top of that ordering, and agenix reactivates on every rebuild, 105 times in one measured week on this machine, so the supervisor would be stopped every one of those times and the X-RestartIfChanged opt-out would buy nothing";

  clawde-agent-tmux-session-defaults-to-clawde =
    mkEvalCheck "clawde-agent-tmux-session-defaults-to-clawde"
      (cfgWithClawdeAgent.clawde.agents.test-agent.tmuxSession == "clawde")
      "clawde.agents.<name>.tmuxSession must default to 'clawde' so agents without an explicit session share the canonical clawde tmux session";

  clawde-agent-tmux-session-accepts-custom-value =
    mkEvalCheck "clawde-agent-tmux-session-accepts-custom-value"
      (
        cfgWithClawdeAgentsOnDistinctSessions.clawde.agents.agent-on-custom-session.tmuxSession
        == "custom-session-for-this-agent"
      )
      "clawde.agents.<name>.tmuxSession must round-trip a custom session name set in the config";

  clawde-agents-can-live-on-distinct-tmux-sessions =
    mkEvalCheck "clawde-agents-can-live-on-distinct-tmux-sessions"
      (
        cfgWithClawdeAgentsOnDistinctSessions.clawde.agents.agent-on-default-session.tmuxSession
        != cfgWithClawdeAgentsOnDistinctSessions.clawde.agents.agent-on-custom-session.tmuxSession
      )
      "two agents with different tmuxSession values must keep distinct session names so the clawde supervisor can host them in separate tmux sessions";
}
