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

  clawde-yields-memory-to-the-interactive-desktop =
    mkEvalCheck "clawde-yields-memory-to-the-interactive-desktop"
      ((clawdeService.Service.MemoryHigh or null) == "5G")
      "clawde.service must carry a MemoryHigh ceiling so the agent fleet, not the browser, is what gets reclaimed under pressure. Unbounded it reached 6.2G holding 56 processes on a 14G machine and pushed roughly a gigabyte of Chrome's renderers into zram, where every tab switch then pays zstd decompression before it paints. The growth is fan-out rather than a leak: every helper measured had a live parent, and the cost is per concurrent session, opencode at a ~700M baseline each plus its own nixd forking two attrset-eval workers plus its own MCP servers, so five sessions multiply into gigabytes. This ceiling only bounds the total and buys the desktop its pages back; it does not reduce the per-session cost, which is why the durable fix is fewer concurrent sessions. MemoryHigh is deliberately the soft knob rather than MemoryMax or MemorySwapMax: it throttles and reclaims without killing, so agents degrade into swap instead of dying, and it applies to the running supervisor on daemon-reload without the restart that would take the tmux server and every agent window down with it";

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
