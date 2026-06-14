{
  config,
  pkgs,
  lib,
  ...
}:
let
  stewardSkillSetDirectory = "${config.home.homeDirectory}/.local/share/claude-skill-sets/steward";

  inherit (config.clawde) stewardLiveCheckoutPayloadPath;

  stewardSkillPayloadSource =
    if stewardLiveCheckoutPayloadPath != null then
      config.lib.file.mkOutOfStoreSymlink stewardLiveCheckoutPayloadPath
    else
      ./payload;

  stewardPackages = (import ./payload/install/default.nix { inherit pkgs; }).packages;

  stewardIsInstantiated = lib.any (name: config.clawde.agents.${name}.type == "steward") (
    builtins.attrNames config.clawde.agents
  );
in
{
  config = lib.mkMerge [
    {
      clawde.agentTypes.steward = {
        defaultModel = "opus";
        defaultPermissionMode = "bypassPermissions";
        defaultDailySessionRotation = true;
        defaultHeartbeatInterval = "*/15 * * * *";
        defaultHeartbeatPrompt = builtins.readFile ./payload/heartbeat-prompt.md;
        defaultHeartbeatGateCommand = "clawde-heartbeat-change-gate --label steward --probe steward-heartbeat-probe";
        defaultDenyToolPatterns = [
          "mcp__chrome-devtools__*"
          "mcp__browser-use__*"
          "mcp__codex__*"
          "mcp__a2a__*"
          "mcp__claude_ai_Gmail__*"
          "mcp__claude_ai_Google_Calendar__*"
          "mcp__claude_ai_Google_Drive__*"
          "mcp__plugin_discord_discord__*"
          "Skill(discord:configure)"
          "Skill(discord:access)"
        ];
        defaultSkillDirectories = [ stewardSkillSetDirectory ];
        packages = stewardPackages;
      };
    }
    (lib.mkIf stewardIsInstantiated {
      home.packages = stewardPackages;

      home.file.".local/share/claude-skill-sets/steward/.claude/skills/steward".source =
        stewardSkillPayloadSource;
    })
  ];
}
