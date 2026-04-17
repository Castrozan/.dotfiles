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

  cfg =
    (inputs.home-manager.lib.homeManagerConfiguration {
      inherit pkgs;
      modules = [
        self.homeManagerModules.claude-code
        {
          home = {
            username = "test";
            homeDirectory = "/home/test";
            inherit (helpers) stateVersion;
          };
        }
      ];
    }).config;

  cfgWithDiscordAgent =
    (inputs.home-manager.lib.homeManagerConfiguration {
      inherit pkgs;
      modules = [
        self.homeManagerModules.claude-code
        {
          home = {
            username = "test";
            homeDirectory = "/home/test";
            inherit (helpers) stateVersion;
          };
          claude.discordChannel.agents.test-agent = {
            botTokenSecretName = "discord-bot-token-test";
            role = "Test agent";
            personality = "Test personality";
          };
        }
      ];
    }).config;

  discordChannelService = cfgWithDiscordAgent.systemd.user.services.claude-discord-channel;

  fileNames = builtins.attrNames cfg.home.file;

  hasFilePrefix =
    prefix: builtins.any (n: builtins.substring 0 (builtins.stringLength prefix) n == prefix) fileNames;
in
{
  claude-settings-nix-source =
    mkEvalCheck "claude-settings-nix-source"
      (builtins.hasAttr ".claude/settings.json.nix-source" cfg.home.file)
      "settings.json.nix-source should be in home.file (mutable settings.json is seeded from this)";

  claude-hooks-directory =
    mkEvalCheck "claude-hooks-directory" (hasFilePrefix ".claude/hooks/")
      "hooks directory entries should be in home.file";

  claude-skills-directory =
    mkEvalCheck "claude-skills-directory" (hasFilePrefix ".claude/skills/")
      "skills directory entries should be in home.file";

  claude-bin-wrapper =
    mkEvalCheck "claude-bin-wrapper" (builtins.hasAttr ".local/bin/claude" cfg.home.file)
      ".local/bin/claude should be in home.file";

  claude-research-skill =
    mkEvalCheck "claude-research-skill" (builtins.hasAttr ".claude/skills/research" cfg.home.file)
      "research skill should be deployed for claude";

  claude-discord-channel-survives-config-change-restart =
    mkEvalCheck "claude-discord-channel-survives-config-change-restart"
      ((discordChannelService.Unit.X-RestartIfChanged or true) == false)
      "claude-discord-channel.service must set Unit.X-RestartIfChanged=false so home-manager activation does not restart it (restarting kills the tmux server in its cgroup, destroying every session including unrelated ones)";

  claude-discord-channel-kill-mode-process =
    mkEvalCheck "claude-discord-channel-kill-mode-process"
      ((discordChannelService.Service.KillMode or null) == "process")
      "claude-discord-channel.service must set Service.KillMode=process so systemctl stop/restart only kills the supervisor PID; control-group (the default) takes the tmux daemon down with the service";

  claude-discord-channel-no-execstop-kill-session =
    mkEvalCheck "claude-discord-channel-no-execstop-kill-session"
      (!(discordChannelService.Service ? ExecStop))
      "claude-discord-channel.service must not define ExecStop — any tmux kill-session on stop defeats the whole point of surviving restarts";
}
