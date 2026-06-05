{
  pkgs,
  config,
  lib,
  ...
}:
let
  cfg = config.clawde;
  homeDir = config.home.homeDirectory;
  secretsDirectory = "${homeDir}/.secrets";
  agentsUsingDiscord = lib.filterAttrs (_: agent: agent.channel.type == "discord") cfg.agents;
  hasDiscordAgents = agentsUsingDiscord != { };

  discordAdapterInstructions = builtins.readFile ./instructions/discord-runtime.md;

  updateClaudePluginsMarketplace = pkgs.writeShellScript "update-claude-plugins-marketplace" ''
    export MARKETPLACE_DIR=${lib.escapeShellArg "${homeDir}/.claude/plugins/marketplaces/claude-plugins-official"}
    export GIT_BIN=${pkgs.git}/bin/git
    ${builtins.readFile ./scripts/update-claude-plugins-marketplace.sh}
  '';

  seedDiscordWorkspaceScript = pkgs.writeShellScript "seed-one-workspace-discord" (
    builtins.readFile ../../scripts/seed-one-workspace.sh
  );

  injectOneSecretScript = pkgs.writeShellScript "inject-one-discord-bot-token" (
    builtins.readFile ../../scripts/inject-one-secret.sh
  );

  waitForSecretScript = pkgs.writeShellScript "wait-for-discord-bot-token-secret" (
    builtins.readFile ./scripts/wait-for-secret.sh
  );

  discordChannelEnvDirectoryFor = name: "${homeDir}/.claude/channels/discord/${name}";
in
{
  options.clawde.agents = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options.channel.discord = lib.mkOption {
          type = lib.types.submodule {
            options.botTokenSecretName = lib.mkOption {
              type = lib.types.nullOr lib.types.str;
              default = null;
              description = "Name of the decrypted secret file in ~/.secrets/ that holds the Discord bot token.";
            };
          };
          default = { };
          description = "Discord adapter-specific options. Used only when channel.type = 'discord'.";
        };
      }
    );
  };

  config = {
    clawde.channelAdapters.discord = {
      instructions = discordAdapterInstructions;
      launchFlags = _: "--channels plugin:discord@claude-plugins-official";
      environmentSetterFor =
        agent:
        if agent.channel.discord.botTokenSecretName != null then
          let
            tokenFile = lib.escapeShellArg "${secretsDirectory}/${agent.channel.discord.botTokenSecretName}";
          in
          "${waitForSecretScript} ${tokenFile} && DISCORD_BOT_TOKEN=$(cat ${tokenFile}) "
        else
          "";
      agentActivationScriptFor =
        {
          name,
          agent,
          workspaceDirectory,
          claudeBinary,
        }:
        let
          secretInjectionLine =
            if agent.channel.discord.botTokenSecretName != null then
              "${injectOneSecretScript} ${lib.escapeShellArg "${secretsDirectory}/${agent.channel.discord.botTokenSecretName}"} ${lib.escapeShellArg (discordChannelEnvDirectoryFor name)} DISCORD_BOT_TOKEN"
            else
              "";
        in
        ''
          ${seedDiscordWorkspaceScript} ${lib.escapeShellArg workspaceDirectory} ${lib.escapeShellArg claudeBinary}
          ${secretInjectionLine}
        '';
      preActivation = if hasDiscordAgents then "run ${updateClaudePluginsMarketplace}" else null;
    };
  };
}
