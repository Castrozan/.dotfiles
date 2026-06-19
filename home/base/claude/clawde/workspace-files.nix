{
  config,
  lib,
  pkgs,
  ...
}:
let
  helpers = import ./lib.nix { inherit pkgs config lib; };
  inherit (helpers)
    cfg
    hasAgents
    homeDir
    agentNames
    agentWorkspaceDirectory
    effectiveAgentByName
    ;

  workspaceRelativeToHome = name: lib.removePrefix "${homeDir}/" (agentWorkspaceDirectory name);

  enforceDiscordReplyStopHook = pkgs.writeShellScript "enforce-discord-reply-stop-hook" ''
    exec ${pkgs.python312}/bin/python3 ${./channel-adapters/discord/scripts/enforce-discord-reply-stop-hook.py} "$@"
  '';

  agentIsDiscord = name: cfg.agents.${name}.channel.type == "discord";

  agentSettings =
    name:
    let
      agent = effectiveAgentByName name;
      denySettings = lib.optionalAttrs (agent.denyToolPatterns != [ ]) {
        permissions.deny = agent.denyToolPatterns;
      };
      discordAgentSettings = lib.optionalAttrs (agentIsDiscord name) {
        hooks.Stop = [
          {
            hooks = [
              {
                type = "command";
                command = "${enforceDiscordReplyStopHook}";
              }
            ];
          }
        ];
        enabledPlugins."discord@claude-plugins-official" = true;
      };
    in
    lib.recursiveUpdate denySettings discordAgentSettings;

  agentWorkspaceSettingsFiles = lib.listToAttrs (
    map (name: {
      name = "${workspaceRelativeToHome name}/.claude/settings.json";
      value = {
        text = builtins.toJSON (agentSettings name);
      };
    }) (builtins.filter (name: agentSettings name != { }) agentNames)
  );
in
{
  config = lib.mkIf hasAgents {
    home.file = agentWorkspaceSettingsFiles;
  };
}
