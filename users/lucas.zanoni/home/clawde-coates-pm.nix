{ config, ... }:
let
  inherit (config.home) homeDirectory;
  dotfilesAgentsSkillsDirectory = "${homeDirectory}/.dotfiles/agents/skills";
in
{
  clawde.agents.coates-pm = {
    model = "opus";
    permissionMode = "bypassPermissions";
    skillDirectories = [
      "${dotfilesAgentsSkillsDirectory}/jira"
      "${dotfilesAgentsSkillsDirectory}/glab"
      "${dotfilesAgentsSkillsDirectory}/daily-report"
    ];
    activeHoursStart = 8;
    activeHoursEnd = 20;
    dailySessionRotation = true;
    heartbeatInterval = "3,33 * * * *";
    heartbeatPrompt = "Heartbeat tick. Read .pm/HEARTBEAT.md at your workspace. If there is no active queue, exit silently. If a task is in flight, continue it. If a previous task finished without a status update, write one. Refresh the repos-in-mandate list if you have not in the last 7 days.";
    personality = builtins.readFile ./agents/coates-pm-personality.md;
    channel = {
      type = "pm";
      pm.projectDirectory = "${homeDirectory}/repo/coates-pm";
    };
  };
}
