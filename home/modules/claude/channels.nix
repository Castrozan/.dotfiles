{
  pkgs,
  config,
  lib,
  ...
}:
let
  homeDir = config.home.homeDirectory;
  username = config.home.username;
  secretsDirectory = "${homeDir}/.secrets";
  discordBotTokenSecretFile = "${secretsDirectory}/discord-bot-token-claude";
  discordChannelStateDirectory = "${homeDir}/.claude/channels/discord";
  discordChannelEnvFile = "${discordChannelStateDirectory}/.env";
  claudeBinary = "${homeDir}/.local/bin/claude";
  tmuxSessionName = "claude-discord";

  nixSystemPaths = lib.concatStringsSep ":" [
    "${pkgs.tmux}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${username}/bin"
    "${homeDir}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

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

  claudeDiscordChannelServiceScript = pkgs.writeShellScript "claude-discord-channel-service" ''
    set -euo pipefail

    if [ ! -f "${discordChannelEnvFile}" ]; then
      echo "Discord channel not configured" >&2
      exit 1
    fi

    if ${pkgs.tmux}/bin/tmux has-session -t "${tmuxSessionName}" 2>/dev/null; then
      ${pkgs.tmux}/bin/tmux kill-session -t "${tmuxSessionName}"
    fi

    ${pkgs.tmux}/bin/tmux new-session -d -s "${tmuxSessionName}" -n discord \
      "${claudeBinary} --channels plugin:discord@claude-plugins-official"

    while ${pkgs.tmux}/bin/tmux has-session -t "${tmuxSessionName}" 2>/dev/null; do
      sleep 10
    done
  '';

  claudeDiscordChannelSessionStarter = pkgs.writeShellScriptBin "claude-discord-channel" ''
    set -euo pipefail

    if [ ! -f "${discordChannelEnvFile}" ]; then
      echo "Discord channel not configured. Encrypt bot token to secrets/bot-tokens/discord-bot-token-claude.age" >&2
      exit 1
    fi

    if ${pkgs.tmux}/bin/tmux has-session -t "${tmuxSessionName}" 2>/dev/null; then
      echo "Session ${tmuxSessionName} already running. Attach with: tmux attach -t ${tmuxSessionName}" >&2
      exit 0
    fi

    systemctl --user restart claude-discord-channel.service
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
  };

  systemd.user.services.claude-discord-channel = {
    Unit = {
      Description = "Claude Code Discord Channel (persistent tmux session)";
      After = [ "network.target" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${claudeDiscordChannelServiceScript}";
      ExecStop = "-${pkgs.tmux}/bin/tmux kill-session -t ${tmuxSessionName}";
      Restart = "always";
      RestartSec = "5s";
      Environment = [
        "PATH=${nixSystemPaths}"
        "HOME=${homeDir}"
        "TMUX_TMPDIR=/run/user/1000"
        "XDG_RUNTIME_DIR=/run/user/1000"
      ];
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };
}
