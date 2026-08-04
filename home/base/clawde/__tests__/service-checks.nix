{
  mkEvalCheck,
  helpers,
  self,
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
  clawde-survives-config-change-restart =
    mkEvalCheck "clawde-survives-config-change-restart"
      (!(clawdeService.Unit.X-RestartIfChanged or true))
      "clawde.service must set Unit.X-RestartIfChanged=false so home-manager activation does not restart it (restarting kills the tmux server in its cgroup, destroying every agent window)";

  clawde-carries-a-runaway-memory-backstop =
    mkEvalCheck "clawde-carries-a-runaway-memory-backstop"
      ((clawdeService.Service.MemoryHigh or null) == "8G")
      "clawde.service must carry a MemoryHigh backstop so unbounded fan-out cannot take the whole 14G machine and push the browser's renderers into zram, where every tab switch then pays zstd decompression before it paints. The growth is fan-out rather than a leak: every helper measured had a live parent, and the cost is per concurrent session, opencode at a ~700M baseline each plus its own nixd forking two attrset-eval workers plus its own MCP servers, so five sessions multiply into gigabytes. The value is sized as a backstop rather than a daily throttle because this cgroup is not the fleet alone: clawde.service hosts the shared herdr server, so the human's interactive session and every command it launches, a rebuild included, are accounted here too. A 5G ceiling against a 6.2G resting fleet was measured producing 44k throttle events, 22% full PSI stall, and 8.6G relocated into swap until system swap was exhausted, which starves the desktop rather than freeing it, since MemoryHigh without MemorySwapMax moves pages instead of reducing them. 8G clears the resting fleet plus a concurrent rebuild and only engages on genuine runaway. MemoryHigh stays the soft knob rather than MemoryMax or MemorySwapMax: it throttles and reclaims without killing, so agents degrade into swap instead of dying, and it applies to the running supervisor on daemon-reload without the restart that would take the tmux server and every agent window down with it. It bounds the total, it does not reduce the per-session cost, so the durable fix remains fewer concurrent sessions";

  clawde-kill-mode-process =
    mkEvalCheck "clawde-kill-mode-process" ((clawdeService.Service.KillMode or null) == "process")
      "clawde.service must set Service.KillMode=process so systemctl stop/restart only kills the supervisor PID; control-group (the default) takes the tmux daemon down with the service";

  clawde-no-execstop-kill-session =
    mkEvalCheck "clawde-no-execstop-kill-session" (!(clawdeService.Service ? ExecStop))
      "clawde.service must not define ExecStop - any tmux kill-session on stop defeats the whole point of surviving restarts";

  clawde-does-not-require-agenix =
    mkEvalCheck "clawde-does-not-require-agenix"
      (!(builtins.elem "agenix.service" (clawdeService.Unit.Requires or [ ])))
      "clawde.service must not Requires=agenix.service - every rebuild reactivates agenix and Requires propagates the deactivation, killing the tmux server. Use Wants=agenix.service plus After=agenix.service instead";

  clawde-wants-agenix =
    mkEvalCheck "clawde-wants-agenix" (builtins.elem "agenix.service" (clawdeService.Unit.Wants or [ ]))
      "clawde.service must Wants=agenix.service so agenix is started on boot but its restart does not bring the clawde supervisor down";

  clawde-after-agenix =
    mkEvalCheck "clawde-after-agenix" (builtins.elem "agenix.service" (clawdeService.Unit.After or [ ]))
      "clawde.service must After=agenix.service so the bot tokens are available when the supervisor starts on initial boot";

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
