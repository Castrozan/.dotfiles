{
  pkgs,
  config,
  lib,
  ...
}:
let
  cfg = config.claude.projectAgents;
  homeDir = config.home.homeDirectory;
  inherit (config.home) username;
  claudeBinary = "${homeDir}/.local/bin/claude";
  instructionsFile = ./project-agent/instructions.md;
  hasAgents = cfg.agents != { };
  agentNames = builtins.attrNames cfg.agents;

  nixSystemPaths = lib.concatStringsSep ":" [
    "${pkgs.tmux}/bin"
    "${pkgs.python312}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${username}/bin"
    "${homeDir}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

  tmuxSessionName = name: "pm-${name}";

  buildBootstrapPromptFile =
    name: agent:
    let
      heartbeatTickPrompt = "Heartbeat tick. Read .pm/HEARTBEAT.md. If there are pending tasks with elapsed intervals, work on the highest priority one. If nothing needs attention, do nothing - do not respond or log.";
    in
    pkgs.writeText "project-agent-bootstrap-${name}" ''
      You are a persistent project agent. Read your CLAUDE.md for your identity and instructions. Read .pm/HEARTBEAT.md for pending work.

      Set up your heartbeat loop now: use CronCreate with cron: "${agent.heartbeatInterval}", recurring: true, and this prompt:

      "${heartbeatTickPrompt}"

      After setting up the heartbeat, read .pm/HEARTBEAT.md and act on any pending work. If nothing is pending, report your status and wait for instructions.
    '';

  buildServiceScript =
    name: agent:
    let
      session = tmuxSessionName name;
      bootstrapFile = buildBootstrapPromptFile name agent;
      projectDir = agent.projectDirectory;
    in
    pkgs.writeShellScript "claude-project-agent-${name}" ''
      set -euo pipefail

      SESSION="${session}"
      PROJECT_DIR="${projectDir}"
      PM_DIR="$PROJECT_DIR/.pm"

      # Kill existing session
      ${pkgs.tmux}/bin/tmux kill-session -t "$SESSION" 2>/dev/null || true

      # Seed workspace
      mkdir -p "$PM_DIR"
      if [ ! -f "$PM_DIR/HEARTBEAT.md" ]; then
        printf '# Heartbeat\n\nNo active work.\n' > "$PM_DIR/HEARTBEAT.md"
      fi

      # Resolve persistent session ID (deterministic from agent name)
      SESSION_ID_FILE="$PM_DIR/session-id"
      if [ -f "$SESSION_ID_FILE" ]; then
        SESSION_ID=$(tr -d '[:space:]' < "$SESSION_ID_FILE")
      else
        SESSION_ID=$(${pkgs.python312}/bin/python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, '${name}-project-manager-agent'))")
        printf '%s\n' "$SESSION_ID" > "$SESSION_ID_FILE"
      fi

      # Create tmux session in project directory
      ${pkgs.tmux}/bin/tmux new-session -d -s "$SESSION" -c "$PROJECT_DIR"

      # Launch claude in the tmux pane
      CLAUDE_CMD="${claudeBinary} --model ${agent.model} --name ${name} --dangerously-skip-permissions --append-system-prompt-file ${instructionsFile} --session-id $SESSION_ID"
      ${pkgs.tmux}/bin/tmux send-keys -t "$SESSION" "$CLAUDE_CMD" Enter

      # Wait for claude input prompt
      for i in $(seq 1 30); do
        PANE_CONTENT=$(${pkgs.tmux}/bin/tmux capture-pane -t "$SESSION" -p -S -10 2>/dev/null || true)
        if printf '%s' "$PANE_CONTENT" | grep -q '❯'; then
          break
        fi
        sleep 1
      done

      # Send bootstrap prompt (re-registers heartbeat cron on every start)
      ${pkgs.tmux}/bin/tmux load-buffer "${bootstrapFile}"
      ${pkgs.tmux}/bin/tmux paste-buffer -t "$SESSION"
      ${pkgs.tmux}/bin/tmux send-keys -t "$SESSION" Enter

      # Keep alive while tmux session exists
      while ${pkgs.tmux}/bin/tmux has-session -t "$SESSION" 2>/dev/null; do
        sleep 10
      done
    '';

  seedProjectAgentWorkspaces = pkgs.writeShellScript "seed-project-agent-workspaces" (
    lib.concatMapStringsSep "\n" (
      name:
      let
        agent = cfg.agents.${name};
      in
      ''
        mkdir -p "${agent.projectDirectory}/.pm"
        if [ ! -f "${agent.projectDirectory}/.pm/HEARTBEAT.md" ]; then
          printf '# Heartbeat\n\nNo active work.\n' > "${agent.projectDirectory}/.pm/HEARTBEAT.md"
        fi
      ''
    ) agentNames
  );
in
{
  options.claude.projectAgents.agents = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options = {
          projectDirectory = lib.mkOption {
            type = lib.types.str;
            description = "Absolute path to the project directory (must contain CLAUDE.md)";
          };
          model = lib.mkOption {
            type = lib.types.str;
            default = "opus";
            description = "Claude model alias (opus, sonnet, haiku)";
          };
          heartbeatInterval = lib.mkOption {
            type = lib.types.str;
            default = "3,33 * * * *";
            description = "Cron expression for heartbeat interval (default: minutes 3 and 33 of every hour)";
          };
        };
      }
    );
    default = { };
    description = "Project manager agents - each becomes a persistent Claude Code session with heartbeat loop";
  };

  config = lib.mkIf hasAgents {
    systemd.user.services = lib.mapAttrs' (name: agent: {
      name = "claude-project-agent-${name}";
      value = {
        Unit = {
          Description = "Claude Code project agent: ${name}";
          After = [ "network.target" ];
        };
        Service = {
          Type = "simple";
          ExecStart = "${buildServiceScript name agent}";
          ExecStop = "-${pkgs.tmux}/bin/tmux kill-session -t ${tmuxSessionName name}";
          Restart = "always";
          RestartSec = "10s";
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
    }) cfg.agents;

    home.activation.seedProjectAgentWorkspaces = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${seedProjectAgentWorkspaces}
    '';
  };
}
