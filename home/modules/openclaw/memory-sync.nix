{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;
  cfg = openclaw.memorySync;

  agentWorkspacePath =
    agentName:
    if builtins.hasAttr agentName openclaw.agents then
      openclaw.agents.${agentName}.workspace
    else
      "openclaw/${agentName}";

  rsync = "${pkgs.rsync}/bin/rsync";
  ssh = "${pkgs.openssh}/bin/ssh";

  syncScript = pkgs.writeShellScript "openclaw-memory-sync" ''
    set -euo pipefail

    readonly REMOTE_HOST="${cfg.remoteHost}"
    readonly REMOTE_USER="${cfg.remoteUser}"
    readonly REMOTE_HOME="/home/$REMOTE_USER"
    readonly HOSTNAME="$(hostname)"

    _check_remote_reachable() {
      ${ssh} -o ConnectTimeout=5 -o BatchMode=yes "$REMOTE_HOST" "true" 2>/dev/null
    }

    _ensure_remote_directory() {
      local remote_path="$1"
      ${ssh} -o ConnectTimeout=5 -o BatchMode=yes "$REMOTE_HOST" "mkdir -p '$remote_path'" 2>/dev/null
    }

    _sync_agent_memory() {
      local agent_name="$1"
      local local_dir="$2"
      local remote_dir="$3"

      local local_push_count
      local_push_count=$(${rsync} -az --update --itemize-changes --timeout=10 "$local_dir" "$remote_dir" 2>/dev/null | grep -c '^>' || true)

      local remote_pull_count
      remote_pull_count=$(${rsync} -az --update --itemize-changes --timeout=10 "$remote_dir" "$local_dir" 2>/dev/null | grep -c '^>' || true)

      echo "[memory-sync] $agent_name: pushed=$local_push_count pulled=$remote_pull_count"
    }

    if ! _check_remote_reachable; then
      echo "[memory-sync] $REMOTE_HOST unreachable, skipping all agents"
      exit 0
    fi

    ${lib.concatMapStringsSep "\n" (
      agentName:
      let
        workspace = agentWorkspacePath agentName;
        localMemoryDir = "${homeDir}/${workspace}/memory/";
        remoteMemoryDir = "$REMOTE_USER@$REMOTE_HOST:$REMOTE_HOME/${workspace}/memory/";
      in
      ''
        mkdir -p "${localMemoryDir}"
        _ensure_remote_directory "$REMOTE_HOME/${workspace}/memory"
        _sync_agent_memory "${agentName}" "${localMemoryDir}" "${remoteMemoryDir}"
      ''
    ) cfg.agents}
  '';
in
{
  options.openclaw.memorySync = {
    enable = lib.mkEnableOption "bidirectional memory sync between machines";

    remoteHost = lib.mkOption {
      type = lib.types.str;
      description = "SSH host alias for the remote machine";
    };

    remoteUser = lib.mkOption {
      type = lib.types.str;
      description = "Username on the remote machine (for home path construction)";
    };

    agents = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = lib.attrNames openclaw.enabledAgents;
      description = "Agent names whose memory directories to sync. Defaults to all enabled agents.";
    };

    interval = lib.mkOption {
      type = lib.types.str;
      default = "5min";
      description = "Systemd timer interval for sync";
    };
  };

  config = lib.mkIf (cfg.enable && cfg.agents != [ ]) {
    systemd.user.services.openclaw-memory-sync = {
      Unit = {
        Description = "OpenClaw agent memory bidirectional sync";
        After = [ "network.target" ];
      };
      Service = {
        Type = "oneshot";
        ExecStart = "${syncScript}";
      };
    };

    systemd.user.timers.openclaw-memory-sync = {
      Unit.Description = "OpenClaw agent memory sync timer";
      Timer = {
        OnBootSec = "2min";
        OnUnitActiveSec = cfg.interval;
      };
      Install.WantedBy = [ "timers.target" ];
    };
  };
}
