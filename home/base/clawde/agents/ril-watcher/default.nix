{ config, ... }:
let
  rilWatcherSkillSetDirectory = "${config.home.homeDirectory}/.local/share/claude-skill-sets/ril-watcher";
in
{
  claudeCuratedSkillSets.ril-watcher = [
    "ril"
    "nix"
    "git"
    "worktrees"
    "test"
    "twitter"
    "youtube"
    "research"
    "browser"
  ];

  clawde.agents.ril-watcher = {
    harness = "codex";
    launchOnTrigger = true;
    launchGateIntervalSeconds = 1800;
    heartbeatGateCommand = "clawde-heartbeat-change-gate --label ril --retries-while-pending 2 --probe 'ril probe'";
    heartbeatPrompt = builtins.readFile ./run-once-prompt.md;
    personality = builtins.readFile ./personality.md;
    skillDirectories = [
      rilWatcherSkillSetDirectory
      "${config.home.homeDirectory}/.dotfiles"
      "${config.home.homeDirectory}/vault"
    ];
  };
}
