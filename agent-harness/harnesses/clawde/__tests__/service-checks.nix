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
      "clawde.service must set Unit.X-RestartIfChanged=false and Service.KillMode=process and must declare no ExecStop, three attributes carrying one invariant: stopping the supervisor never takes the fleet with it. KillMode=process is the part that actually carries it, since systemd then kills the supervisor pid alone and journals every survivor as 'Unit process N remains running after unit stopped', one herdr pid having been observed surviving two such stops four days apart, where control-group (the default) would take the whole cgroup, which here is the shared herdr server, every agent wrapper, every harness under them and the human's own session. An ExecStop undoes that by hand, because any kill-session on stop destroys exactly the windows KillMode just spared. X-RestartIfChanged=false only suppresses churn, keeping activation from cutting supervision on every rebuild that touches an agent's config, and it guarantees nothing: three restarts got through 105 activations in one measured week on this machine, so a rollout reads the fleet's live store paths rather than inferring them from the flag";

  clawde-carries-a-runaway-memory-backstop =
    mkEvalCheck "clawde-carries-a-runaway-memory-backstop"
      ((clawdeService.Service.MemoryHigh or null) == "8G")
      "clawde.service must carry a MemoryHigh backstop so unbounded fan-out cannot take the whole 14G machine and push the browser's renderers into zram, where every tab switch then pays zstd decompression before it paints. The growth is fan-out rather than a leak: every helper measured had a live parent, and the cost is per concurrent session, opencode at a ~700M baseline each plus its own nixd forking two attrset-eval workers plus its own MCP servers, so five sessions multiply into gigabytes. The value is sized as a backstop rather than a daily throttle because this cgroup is not the fleet alone: clawde.service hosts the shared herdr server, so the human's interactive session and every command it launches, a rebuild included, are accounted here too. A 5G ceiling against a 6.2G resting fleet was measured producing 44k throttle events, 22% full PSI stall, and 8.6G relocated into swap until system swap was exhausted, which starves the desktop rather than freeing it, since MemoryHigh without MemorySwapMax moves pages instead of reducing them. 8G clears the resting fleet plus a concurrent rebuild and only engages on genuine runaway. MemoryHigh stays the soft knob rather than MemoryMax or MemorySwapMax: it throttles and reclaims without killing, so agents degrade into swap instead of dying, and it applies to the running supervisor on daemon-reload, so raising or lowering the ceiling never needs the unit stopped at all. It bounds the total, it does not reduce the per-session cost, so the durable fix remains fewer concurrent sessions";

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
