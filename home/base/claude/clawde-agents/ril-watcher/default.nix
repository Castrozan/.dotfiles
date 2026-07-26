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
  ];

  clawde.agents.ril-watcher = {
    model = "opus";
    permissionMode = "bypassPermissions";
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
    denyToolPatterns = [
      "Bash(gh pr merge:*)"
      "Bash(ril record:*)"
      "Bash(rebuild:*)"
      "Bash(nixos-rebuild:*)"
      "Bash(darwin-rebuild:*)"
      "Bash(sudo:*)"
      "Bash(rm:*)"
      "Bash(dd:*)"
      "Bash(mkfs:*)"
      "Bash(shutdown:*)"
      "Bash(reboot:*)"
      "Skill(discord:configure)"
      "Skill(discord:access)"
      "mcp__claude_ai_Gmail__*"
      "mcp__claude_ai_Google_Calendar__*"
      "mcp__claude_ai_Google_Drive__*"
    ];
  };
}
