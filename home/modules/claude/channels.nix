{
  pkgs,
  config,
  lib,
  ...
}:
let
  homeDir = config.home.homeDirectory;
  secretsDirectory = "${homeDir}/.secrets";
  discordBotTokenSecretFile = "${secretsDirectory}/discord-bot-token-claude";
  discordChannelStateDirectory = "${homeDir}/.claude/channels/discord";
  discordChannelEnvFile = "${discordChannelStateDirectory}/.env";

  injectDiscordBotTokenFromAgenix = pkgs.writeShellScript "inject-claude-discord-bot-token" ''
    set -euo pipefail

    if [ ! -f "${discordBotTokenSecretFile}" ]; then
      exit 0
    fi

    TOKEN="$(cat "${discordBotTokenSecretFile}")"
    if [ -z "$TOKEN" ]; then
      exit 0
    fi

    mkdir -p "${discordChannelStateDirectory}"
    printf 'DISCORD_BOT_TOKEN=%s\n' "$TOKEN" > "${discordChannelEnvFile}"
    chmod 600 "${discordChannelEnvFile}"
  '';

  claudeDiscordChannelSessionStarter = pkgs.writeShellScriptBin "claude-discord-channel" ''
    set -euo pipefail

    SESSION_NAME="claude-discord"

    if [ ! -f "${discordChannelEnvFile}" ]; then
      echo "Discord channel not configured. Encrypt bot token to secrets/bot-tokens/discord-bot-token-claude.age" >&2
      exit 1
    fi

    if ${pkgs.tmux}/bin/tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
      echo "Session $SESSION_NAME already running" >&2
      exit 0
    fi

    ${pkgs.tmux}/bin/tmux new-session -d -s "$SESSION_NAME" -n claude-discord \
      "${homeDir}/.local/bin/claude --channels plugin:discord@claude-plugins-official"
  '';

  claudeDiscordChannelAutostart = pkgs.writeShellScript "claude-discord-channel-autostart" ''
    set -euo pipefail

    if [ ! -f "${discordChannelEnvFile}" ]; then
      exit 0
    fi

    if ${pkgs.tmux}/bin/tmux has-session -t claude-discord 2>/dev/null; then
      exit 0
    fi

    ${claudeDiscordChannelSessionStarter}/bin/claude-discord-channel
  '';

  updateClaudePluginsMarketplace = pkgs.writeShellScript "update-claude-plugins-marketplace" ''
    set -euo pipefail
    MARKETPLACE_DIR="${homeDir}/.claude/plugins/marketplaces/claude-plugins-official"

    if [ ! -d "$MARKETPLACE_DIR/.git" ]; then
      exit 0
    fi

    cd "$MARKETPLACE_DIR"
    ${pkgs.git}/bin/git pull --ff-only origin main 2>/dev/null || true
  '';
in
{
  home = {
    packages = [ claudeDiscordChannelSessionStarter ];

    activation.injectClaudeDiscordBotToken = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${injectDiscordBotTokenFromAgenix}
    '';

    activation.updateClaudePluginsMarketplace = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${updateClaudePluginsMarketplace}
    '';

    activation.autostartClaudeDiscordChannel = lib.hm.dag.entryAfter [
      "writeBoundary"
      "injectClaudeDiscordBotToken"
      "updateClaudePluginsMarketplace"
    ] ''
      run ${claudeDiscordChannelAutostart}
    '';
  };
}
