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

  syncScript = pkgs.writeShellScript "openclaw-memory-sync" ''
    set -euo pipefail

    REMOTE_HOST="${cfg.remoteHost}"
    REMOTE_HOME="/home/${cfg.remoteUser}"

    ${lib.concatMapStringsSep "\n" (
      agentName:
      let
        workspace = agentWorkspacePath agentName;
        localMemoryDir = "${homeDir}/${workspace}/memory/";
        remoteMemoryDir = "${cfg.remoteUser}@${cfg.remoteHost}:$REMOTE_HOME/${workspace}/memory/";
      in
      ''
        mkdir -p "${localMemoryDir}"

        if ! ${pkgs.openssh}/bin/ssh -o ConnectTimeout=5 -o BatchMode=yes "${cfg.remoteHost}" "mkdir -p '$REMOTE_HOME/${workspace}/memory'" 2>/dev/null; then
          echo "[memory-sync] ${agentName}: remote ${cfg.remoteHost} unreachable, skipping"
        else
          ${pkgs.rsync}/bin/rsync -az --update --timeout=10 "${localMemoryDir}" "${remoteMemoryDir}" 2>/dev/null || true
          ${pkgs.rsync}/bin/rsync -az --update --timeout=10 "${remoteMemoryDir}" "${localMemoryDir}" 2>/dev/null || true
          echo "[memory-sync] ${agentName}: synced with ${cfg.remoteHost}"
        fi
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
      default = [ ];
      description = "Agent names whose memory directories to sync. Agents need not be declared locally — uses openclaw/<name> as workspace fallback for remote-only agents.";
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
