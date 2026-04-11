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
  instructionsFile = ./instructions.md;
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

  buildAgentLaunchCommand =
    name: agent:
    let
      modelFlag = "--model ${agent.model}";
      nameFlag = "--name ${name}";
      sessionIdFlag = "--session-id ${agent.sessionId}";
      instructionsFlag = "--append-system-prompt-file ${instructionsFile}";
      permissionsFlag = "--dangerously-skip-permissions";
    in
    "cd ${agent.projectDirectory} && ${claudeBinary} ${modelFlag} ${nameFlag} ${permissionsFlag} ${sessionIdFlag} ${instructionsFlag}";

  buildAgentServiceScript =
    name: agent:
    let
      tmuxSessionName = name;
    in
    pkgs.writeShellScript "project-agent-${name}-service" ''
      set -euo pipefail

      PM_DIR="${agent.projectDirectory}/.pm"
      mkdir -p "$PM_DIR"
      if [ ! -f "$PM_DIR/HEARTBEAT.md" ]; then
        printf '# Heartbeat\n\nNo active work.\n' > "$PM_DIR/HEARTBEAT.md"
      fi
      if [ ! -f "$PM_DIR/session-id" ]; then
        printf '%s\n' "${agent.sessionId}" > "$PM_DIR/session-id"
      fi

      if ${pkgs.tmux}/bin/tmux has-session -t "${tmuxSessionName}" 2>/dev/null; then
        ${pkgs.tmux}/bin/tmux kill-session -t "${tmuxSessionName}"
      fi

      ${pkgs.tmux}/bin/tmux new-session -d -s "${tmuxSessionName}" -c "${agent.projectDirectory}" \
        "${buildAgentLaunchCommand name agent}"

      while ${pkgs.tmux}/bin/tmux has-session -t "${tmuxSessionName}" 2>/dev/null; do
        sleep 10
      done
    '';

  generateSessionId = name: builtins.hashString "sha256" "${name}-project-manager-agent";

  formatSessionIdAsUuid =
    hash:
    let
      h = builtins.substring 0 32 hash;
    in
    "${builtins.substring 0 8 h}-${builtins.substring 8 4 h}-${builtins.substring 12 4 h}-${builtins.substring 16 4 h}-${builtins.substring 20 12 h}";
in
{
  options.claude.projectAgents.agents = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule (
        { name, ... }:
        {
          options = {
            projectDirectory = lib.mkOption {
              type = lib.types.str;
              description = "Absolute path to the project directory (must contain CLAUDE.md)";
            };
            model = lib.mkOption {
              type = lib.types.str;
              default = "opus";
              description = "Claude model alias";
            };
            sessionId = lib.mkOption {
              type = lib.types.str;
              default = formatSessionIdAsUuid (generateSessionId name);
              description = "Persistent Claude session UUID (auto-generated from agent name)";
            };
          };
        }
      )
    );
    default = { };
    description = "Persistent project manager agents - each gets a tmux session with systemd auto-restart";
  };

  config = lib.mkIf hasAgents {
    systemd.user.services = lib.listToAttrs (
      map (name: {
        name = "project-agent-${name}";
        value = {
          Unit = {
            Description = "Project agent: ${name}";
            After = [ "network.target" ];
          };
          Service = {
            Type = "simple";
            ExecStart = "${buildAgentServiceScript name cfg.agents.${name}}";
            ExecStop = "-${pkgs.tmux}/bin/tmux kill-session -t ${name}";
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
      }) agentNames
    );
  };
}
