{
  config,
  lib,
  hostname,
  ...
}:
let
  stewardSkillRoot = ../../../../agents/skills/steward;

  stewardNetworkRegistryPath = ../../../../private-config/steward-network.nix;
  stewardNetworkRegistry =
    if builtins.pathExists stewardNetworkRegistryPath then import stewardNetworkRegistryPath else { };

  peerAliases = builtins.filter (alias: alias != hostname) (
    builtins.attrNames stewardNetworkRegistry
  );

  peerEndpoints = builtins.listToAttrs (
    map (alias: {
      name = alias;
      value = {
        inherit (stewardNetworkRegistry.${alias}) host user;
        identity_file = "~/.ssh/id_ed25519";
      };
    }) peerAliases
  );

  peersConfiguration = {
    self = hostname;
    remote_inbox = "clawde/steward/inbox";
    peers = peerEndpoints;
  };

  stewardSkillSetDirectory = "${config.home.homeDirectory}/.local/share/claude-skill-sets/steward";

  personalityWithMachineIdentity =
    builtins.replaceStrings
      [ "@stewardSelf@" "@stewardPeers@" ]
      [ hostname (lib.concatStringsSep ", " peerAliases) ]
      (builtins.readFile (stewardSkillRoot + "/personality.md"));

  stewardDenyToolPatterns = [
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
in
{
  home.file = {
    "clawde/steward/peers.json".text = builtins.toJSON peersConfiguration;

    ".local/share/claude-skill-sets/steward/.claude/skills/steward".source =
      config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/agents/skills/steward";
  };

  clawde.agents.steward = {
    model = "opus";
    permissionMode = "bypassPermissions";
    dailySessionRotation = true;
    heartbeatInterval = "*/15 * * * *";
    heartbeatPrompt = builtins.readFile (stewardSkillRoot + "/heartbeat-prompt.md");
    skillDirectories = [ stewardSkillSetDirectory ];
    denyToolPatterns = stewardDenyToolPatterns;
    personality = personalityWithMachineIdentity;
  };
}
