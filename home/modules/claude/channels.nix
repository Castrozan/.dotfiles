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
  agentWorkspacesBaseDirectory = "${homeDir}/.claude/discord-agents";
  hasAgents = cfg.agents != { };
  agentNames = builtins.attrNames cfg.agents;
  firstAgentName = builtins.head agentNames;

  nixSystemPaths = lib.concatStringsSep ":" [
    "${pkgs.tmux}/bin"
    "${pkgs.python312}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${username}/bin"
    "${homeDir}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

  sharedAutonomyInstructions = ''
    <autonomy>
    You are an autonomous agent. Act decisively and take initiative.

    Try first, ask last. Before asking Lucas anything:
    1. Check your available skills — run skill discovery
    2. Search the codebase with grep/glob
    3. Read --help on any CLI tool
    4. Try the most likely approach
    Only after 2+ genuine attempts, ask for help. Report what you tried, not just "I'm stuck."

    When given a task, do the work. Don't describe what you would do — do it. Don't ask for permission to proceed unless the action is destructive or irreversible. Bias toward action.

    If something fails, note what failed and try an alternative. Iterate until you succeed or exhaust reasonable approaches.
    </autonomy>
  '';

  sharedMemoryInstructions = ''
    <memory>
    You have persistent memory that survives across sessions. Use it aggressively.

    Save to memory when you learn:
    - User preferences, communication style, recurring requests
    - Project context that isn't obvious from code (why decisions were made, constraints)
    - Solutions to problems you solved (so you don't re-discover them)
    - Feedback corrections (so you don't repeat mistakes)

    Read your memory at session start. Your memories are your accumulated wisdom — they make you more effective over time. A well-maintained memory transforms you from a stateless tool into a knowledgeable collaborator.
    </memory>
  '';

  sharedSessionResilienceInstructions = ''
    <session-resilience>
    Sessions can restart at any time. Your conversation history may be lost. Multi-step work survives only if persisted to disk.

    For quick tasks: write current objective and next steps to HEARTBEAT.md in your workspace.
    For big tasks (>5 steps): create a .deep-work/ workspace with plan, progress journal, and context.
    On session start: check HEARTBEAT.md and .deep-work/ — resume from disk without asking the user to re-explain.
    </session-resilience>
  '';

  sharedCommunicationInstructions = ''
    <communication>
    You are talking to users via Discord. Lucas is a senior software engineer. Other users in the guild are his friends or colleagues.
    Be direct and technical. Concise answers. Use markdown for formatting.
    If someone is wrong, tell them. If something fails, fix it — don't just report.
    Respond in the same language the user writes in their message.
    </communication>

    <discord-channel-behavior>
    CRITICAL: When a Discord message arrives, ALWAYS respond immediately using the reply tool. Never ask the operator for permission to respond. Never present interactive choices about whether to reply. You are a Discord bot — every message directed at you gets a response. This is non-negotiable.

    Use the reply MCP tool to send your response back to Discord. The user cannot see your terminal output — only messages sent via the reply tool reach them.
    </discord-channel-behavior>
  '';

  buildAgentClaudeMarkdownContent = name: agent: ''
    ${agent.personality}

    ${sharedAutonomyInstructions}

    ${sharedMemoryInstructions}

    ${sharedSessionResilienceInstructions}

    ${sharedCommunicationInstructions}
  '';

  bootstrapHeartbeatScript = ./scripts/bootstrap-discord-agent-heartbeat;

  agentsWithHeartbeats = lib.filterAttrs (_: agent: agent.heartbeatInterval != null) cfg.agents;
  hasAgentsWithHeartbeats = agentsWithHeartbeats != { };

  buildHeartbeatBootstrapCommand = name: agent: ''
    ${pkgs.python312}/bin/python3 ${bootstrapHeartbeatScript} \
      --session "${tmuxSessionName}" \
      --window ${lib.escapeShellArg name} \
      --interval ${lib.escapeShellArg agent.heartbeatInterval} \
      --prompt ${lib.escapeShellArg agent.heartbeatPrompt} &
  '';

  agentWorkspaceDirectory = name: "${agentWorkspacesBaseDirectory}/${name}";

  buildAgentLaunchCommand =
    name: agent:
    let
      workspace = agentWorkspaceDirectory name;
      tokenFile = "${secretsDirectory}/${agent.botTokenSecretName}";
      channelFlag = "--channels plugin:discord@claude-plugins-official";
      modelFlag = "--model ${agent.model}";
      nameFlag = "--name ${name}";
      skillDirFlags = lib.concatMapStringsSep " " (dir: "--add-dir ${dir}") agent.skillDirectories;
      useWorkspace = agent.workspaceFrom != [ ] || agent.extendWorkspace;
      fromFlags = lib.concatMapStringsSep " " (dir: "--from ${dir}") agent.workspaceFrom;
      extendFlag = if agent.extendWorkspace then "--extend" else "";
      launchBinary =
        if useWorkspace then "claude-workspace ${fromFlags} ${extendFlag} --" else "${claudeBinary}";
      launchFlags = if useWorkspace then "" else skillDirFlags;
    in
    "cd ${workspace} && DISCORD_BOT_TOKEN=$(cat ${tokenFile}) ${launchBinary} ${channelFlag} ${modelFlag} ${nameFlag} ${launchFlags}";

  buildAgentWrapperScript =
    name: agent:
    pkgs.writeShellScript "discord-agent-${name}" ''
      trap 'exit 0' SIGTERM SIGHUP SIGINT

      restart_delay=10
      max_restart_delay=300

      while true; do
        start_time=$(date +%s)
        ${buildAgentLaunchCommand name agent} || true
        end_time=$(date +%s)
        runtime=$((end_time - start_time))

        if [ "$runtime" -gt 60 ]; then
          restart_delay=10
        fi

        echo "[$(date)] Agent ${name} exited after $runtime seconds. Restarting in $restart_delay seconds..."
        sleep "$restart_delay"

        restart_delay=$((restart_delay * 2))
        if [ "$restart_delay" -gt "$max_restart_delay" ]; then
          restart_delay=$max_restart_delay
        fi
      done
    '';

  buildTmuxNewWindowCommand =
    name: agent:
    ''${pkgs.tmux}/bin/tmux new-window -t "${tmuxSessionName}" -n ${name} "${buildAgentWrapperScript name agent}"'';

  heartbeatBootstrapCommands = lib.concatMapStringsSep "\n" (
    name: buildHeartbeatBootstrapCommand name agentsWithHeartbeats.${name}
  ) (builtins.attrNames agentsWithHeartbeats);

  claudeDiscordAgentsServiceScript = pkgs.writeShellScript "claude-discord-agents-service" ''
    set -euo pipefail

    if ${pkgs.tmux}/bin/tmux has-session -t "${tmuxSessionName}" 2>/dev/null; then
      ${pkgs.tmux}/bin/tmux kill-session -t "${tmuxSessionName}"
    fi

    ${pkgs.tmux}/bin/tmux new-session -d -s "${tmuxSessionName}" -n ${firstAgentName} \
      "${buildAgentWrapperScript firstAgentName cfg.agents.${firstAgentName}}"

    ${lib.concatMapStringsSep "\n" (name: buildTmuxNewWindowCommand name cfg.agents.${name}) (
      builtins.tail agentNames
    )}

    ${lib.optionalString hasAgentsWithHeartbeats heartbeatBootstrapCommands}

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

  seedAgentWorkspaces = pkgs.writeShellScript "seed-discord-agent-workspaces" (
    lib.concatMapStringsSep "\n" (
      name:
      let
        workspace = agentWorkspaceDirectory name;
      in
      ''
        mkdir -p "${workspace}"
        if [ ! -f "${workspace}/HEARTBEAT.md" ]; then
          printf '# Heartbeat\n\nNo active work.\n' > "${workspace}/HEARTBEAT.md"
        fi
        if [ ! -f "${workspace}/.claude.json" ]; then
          printf '{"hasCompletedOnboarding":true,"numStartups":1,"installMethod":"native"}\n' > "${workspace}/.claude.json"
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

  agentClaudeMarkdownFiles = lib.listToAttrs (
    map (name: {
      name = ".claude/discord-agents/${name}/CLAUDE.md";
      value = {
        text = buildAgentClaudeMarkdownContent name cfg.agents.${name};
      };
    }) agentNames
  );
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
          skillDirectories = lib.mkOption {
            type = lib.types.listOf lib.types.str;
            default = [ ];
            description = "Absolute paths to skill directories passed as --add-dir to this agent";
          };
          workspaceFrom = lib.mkOption {
            type = lib.types.listOf lib.types.str;
            default = [ ];
            description = "Repo paths loaded via claude-workspace --from (isolated skills, use --extend via extendWorkspace)";
          };
          extendWorkspace = lib.mkOption {
            type = lib.types.bool;
            default = false;
            description = "Pass --extend to claude-workspace to merge base and personal skills";
          };
          personality = lib.mkOption {
            type = lib.types.lines;
            description = "Rich personality and instructions for this agent's CLAUDE.md";
          };
          heartbeatInterval = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Cron expression for heartbeat interval (e.g., '*/5 * * * *'). When set, agent becomes autonomous with a polling loop.";
          };
          heartbeatPrompt = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Prompt sent on each heartbeat tick. Required when heartbeatInterval is set.";
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

        file = agentClaudeMarkdownFiles;

        activation.injectClaudeDiscordBotTokens = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
          run ${injectAllDiscordBotTokens}
        '';

        activation.seedDiscordAgentWorkspaces = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
          run ${seedAgentWorkspaces}
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
