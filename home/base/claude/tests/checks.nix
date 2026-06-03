{
  pkgs,
  lib,
  inputs,
  self,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.claude-code
  ];

  cfgWithClawdeAgent = helpers.homeManagerTestConfiguration [
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

  fileNames = builtins.attrNames cfg.home.file;

  hasFilePrefix =
    prefix: builtins.any (n: builtins.substring 0 (builtins.stringLength prefix) n == prefix) fileNames;
in
{
  claude-settings-nix-source =
    mkEvalCheck "claude-settings-nix-source"
      (builtins.hasAttr ".claude/settings.json.nix-source" cfg.home.file)
      "settings.json.nix-source should be in home.file (mutable settings.json is seeded from this)";

  claude-hooks-deployed-as-single-directory =
    mkEvalCheck "claude-hooks-deployed-as-single-directory"
      (builtins.hasAttr ".claude/hooks" cfg.home.file && !(hasFilePrefix ".claude/hooks/"))
      "hooks must deploy as one atomic directory symlink (home.file.\".claude/hooks\"), never per-file entries; per-file relinking transiently removes helper modules mid-rebuild and breaks hook imports";

  claude-skills-directory =
    mkEvalCheck "claude-skills-directory" (hasFilePrefix ".claude/skills/")
      "skills directory entries should be in home.file";

  claude-bin-wrapper =
    mkEvalCheck "claude-bin-wrapper" (builtins.hasAttr ".local/bin/claude" cfg.home.file)
      ".local/bin/claude should be in home.file";

  claude-research-skill =
    mkEvalCheck "claude-research-skill"
      (builtins.hasAttr ".local/share/claude-skill-sets/personal/.claude/skills/research" cfg.home.file)
      "research skill should be deployed in the personal vault for claude";

  clawde-survives-config-change-restart =
    mkEvalCheck "clawde-survives-config-change-restart"
      (!(clawdeService.Unit.X-RestartIfChanged or true))
      "clawde.service must set Unit.X-RestartIfChanged=false so home-manager activation does not restart it (restarting kills the tmux server in its cgroup, destroying every agent window)";

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

  chrome-devtools-bridge-service-exists =
    let
      bridgeService = cfg.systemd.user.services.chrome-devtools-mcp-bridge;
    in
    mkEvalCheck "chrome-devtools-bridge-service-exists" (
      bridgeService ? Service
    ) "chrome-devtools-mcp-bridge.service must exist as a systemd user service";

  chrome-devtools-bridge-restart-always =
    let
      bridgeService = cfg.systemd.user.services.chrome-devtools-mcp-bridge;
    in
    mkEvalCheck "chrome-devtools-bridge-restart-always" (
      (bridgeService.Service.Restart or null) == "always"
    ) "chrome-devtools-mcp-bridge.service must set Restart=always for auto-recovery";

  chrome-devtools-bridge-wanted-by-default =
    let
      bridgeService = cfg.systemd.user.services.chrome-devtools-mcp-bridge;
    in
    mkEvalCheck "chrome-devtools-bridge-wanted-by-default" (builtins.elem "default.target" (
      bridgeService.Install.WantedBy or [ ]
    )) "chrome-devtools-mcp-bridge.service must be wanted by default.target to start on login";

}
