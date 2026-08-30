{ config, ... }:
{
  clawdeAgentSkillSets.ril-watcher = [
    "ril"
    "nix"
    "coding"
    "twitter"
    "youtube"
    "research"
    "browser"
  ];

  clawde.agents.ril-watcher = {
    harness = "claude";
    model = "haiku";
    launchOnTrigger = true;
    launchGateIntervalSeconds = 1800;
    heartbeatGateCommand = "clawde-heartbeat-change-gate --label ril --retries-while-pending 2 --probe 'ril probe'";
    heartbeatPrompt = builtins.readFile ./run-once-prompt.md;
    personality = builtins.readFile ./personality.md;
    skillDirectories = [
      config.clawdeAgentSkillSetDirectories.ril-watcher
      "${config.home.homeDirectory}/.dotfiles"
      "${config.home.homeDirectory}/vault"
    ];
  };
}
