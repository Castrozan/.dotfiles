{
  pkgs,
  config,
  lib,
  ...
}:
let
  cfg = config.claude.discordChannel;
  homeDir = config.home.homeDirectory;
  inherit (config.home) username;
  secretsDirectory = "${homeDir}/.secrets";
  claudeBinary = "${homeDir}/.local/bin/claude";
  tmuxSessionName = "claude-discord";
  hasAgents = cfg.agents != { };
  agentNames = builtins.attrNames cfg.agents;
  firstAgentName = builtins.head agentNames;

  nixSystemPaths = lib.concatStringsSep ":" [
    "${pkgs.tmux}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${username}/bin"
    "${homeDir}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

  buildAgentLaunchCommand =
    name: agent:
    let
      tokenFile = "${secretsDirectory}/${agent.botTokenSecretName}";
      channelFlag = "--channels plugin:discord@claude-plugins-official";
      modelFlag = "--model ${agent.model}";
      nameFlag = "--name ${name}";
      promptFlag = "--append-system-prompt 'You are ${name}. Your role: ${agent.role}'";
    in
    "DISCORD_BOT_TOKEN=\\$(cat ${tokenFile}) ${claudeBinary} ${channelFlag} ${modelFlag} ${nameFlag} ${promptFlag}";

  buildTmuxNewWindowCommand =
    name: agent:
    ''${pkgs.tmux}/bin/tmux new-window -t "${tmuxSessionName}" -n ${name} "${buildAgentLaunchCommand name agent}"'';

  claudeDiscordAgentsServiceScript = pkgs.writeShellScript "claude-discord-agents-service" ''
    set -euo pipefail

    if ${pkgs.tmux}/bin/tmux has-session -t "${tmuxSessionName}" 2>/dev/null; then
      ${pkgs.tmux}/bin/tmux kill-session -t "${tmuxSessionName}"
    fi

    ${pkgs.tmux}/bin/tmux new-session -d -s "${tmuxSessionName}" -n ${firstAgentName} \
      "${buildAgentLaunchCommand firstAgentName cfg.agents.${firstAgentName}}"

    ${lib.concatMapStringsSep "\n" (name: buildTmuxNewWindowCommand name cfg.agents.${name}) (
      builtins.tail agentNames
    )}

    while ${pkgs.tmux}/bin/tmux has-session -t "${tmuxSessionName}" 2>/dev/null; do
      sleep 10
    done
  '';

  claudeDiscordSessionStarter = pkgs.writeShellScriptBin "claude-discord-channel" ''
    set -euo pipefail

    if ${pkgs.tmux}/bin/tmux has-session -t "${tmuxSessionName}" 2>/dev/null; then
      echo "Session ${tmuxSessionName} already running. Attach with: tmux attach -t ${tmuxSessionName}" >&2
      exit 0
    fi

    systemctl --user restart claude-discord-channel.service
  '';

  injectAllDiscordBotTokens = pkgs.writeShellScript "inject-claude-discord-bot-tokens" (
    lib.concatMapStringsSep "\n" (
      name:
      let
        agent = cfg.agents.${name};
        tokenFile = "${secretsDirectory}/${agent.botTokenSecretName}";
        envDir = "${homeDir}/.claude/channels/discord/${name}";
        envFile = "${envDir}/.env";
      in
      ''
        if [ -f "${tokenFile}" ]; then
          TOKEN="$(cat "${tokenFile}")"
          if [ -n "$TOKEN" ]; then
            mkdir -p "${envDir}"
            printf 'DISCORD_BOT_TOKEN=%s\n' "$TOKEN" > "${envFile}"
            chmod 600 "${envFile}"
          fi
        fi
      ''
    ) agentNames
  );

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
  options.claude.discordChannel.agents = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options = {
          botTokenSecretName = lib.mkOption {
            type = lib.types.str;
            description = "Name of the decrypted secret file in ~/.secrets/";
          };
          role = lib.mkOption {
            type = lib.types.str;
            description = "Agent role description injected as system prompt";
          };
          model = lib.mkOption {
            type = lib.types.str;
            default = "sonnet";
            description = "Claude model alias (opus, sonnet, haiku)";
          };
        };
      }
    );
    default = { };
    description = "Discord channel agents — each becomes a tmux window in the claude-discord session";
  };

  config = lib.mkMerge [
    {
      home.activation.updateClaudePluginsMarketplace = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${updateClaudePluginsMarketplace}
      '';
    }

    (lib.mkIf hasAgents {
      home = {
        packages = [ claudeDiscordSessionStarter ];

        activation.injectClaudeDiscordBotTokens = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
          run ${injectAllDiscordBotTokens}
        '';
      };

      systemd.user.services.claude-discord-channel = {
        Unit = {
          Description = "Claude Code Discord agents (persistent tmux session)";
          After = [ "network.target" ];
        };

        Service = {
          Type = "simple";
          ExecStart = "${claudeDiscordAgentsServiceScript}";
          ExecStop = "-${pkgs.tmux}/bin/tmux kill-session -t ${tmuxSessionName}";
          Restart = "always";
          RestartSec = "5s";
          Environment = [
            "PATH=${nixSystemPaths}"
            "HOME=${homeDir}"
            "TMUX_TMPDIR=%t"
            "XDG_RUNTIME_DIR=%t"
          ];
        };

        Install = {
          WantedBy = [ "default.target" ];
        };
      };
    })
  ];
}
