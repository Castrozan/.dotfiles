{ config, ... }:
{
  clawdeAgentSkillSets.ril-watcher = [
    "ril"
    "forge"
    "browser"
    "desktop"
    "research"
  ];

  clawde.agents.ril-watcher = {
    harness = "claude";
    model = "sonnet";
    permissionMode = "bypassPermissions";
    reasoningEffort = "high";
    launchOnTrigger = true;
    dailySessionRotation = true;
    launchGateIntervalSeconds = 1800;
    heartbeatGateCommand = "clawde-heartbeat-change-gate --label ril --retries-while-pending 2 --probe 'ril probe'";
    heartbeatPrompt = builtins.readFile ./prompt.md;
    personality = builtins.readFile ./personality.md;
    skillDirectories = [
      config.clawdeAgentSkillSetDirectories.ril-watcher
      "${config.home.homeDirectory}/.dotfiles"
      "${config.home.homeDirectory}/vault"
    ];
  };
}
