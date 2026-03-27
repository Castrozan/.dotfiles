{ config, lib, ... }:

let
  dotfilesDir = "${config.home.homeDirectory}/.dotfiles";

  nixDaemonMemoryLimitDropinPath = "/etc/systemd/system/nix-daemon.service.d/memory-limit.conf";
  nixDaemonMemoryLimitDropinContent = ''
    [Service]
    MemoryHigh=60%
    MemoryMax=75%
  '';
in
{
  home.activation.setupOomProtection = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    PATH="/usr/bin:/usr/sbin:/sbin:$PATH"

    if [ -f /etc/NIXOS ]; then
      $VERBOSE_ECHO "Skipping OOM protection setup on NixOS"
    elif command -v earlyoom >/dev/null 2>&1 \
      && grep -q "ALGO=zstd" /etc/default/zramswap 2>/dev/null \
      && grep -q "PERCENT=50" /etc/default/zramswap 2>/dev/null \
      && grep -q "\-m 10" /etc/default/earlyoom 2>/dev/null \
      && [ "$(sysctl -n vm.swappiness 2>/dev/null)" = "150" ]; then
      $VERBOSE_ECHO "OOM protection already configured"
    else
      echo "Setting up OOM protection (requires sudo)..."
      sudo "${dotfilesDir}/home/modules/system/scripts/setup-oom-protection"
    fi
  '';

  home.activation.setupNixDaemonMemoryLimit = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    PATH="/usr/bin:/usr/sbin:/sbin:$PATH"

    if [ -f /etc/NIXOS ]; then
      $VERBOSE_ECHO "Skipping nix-daemon memory limit on NixOS (managed in configuration.nix)"
    elif [ -f "${nixDaemonMemoryLimitDropinPath}" ] \
      && grep -q "MemoryHigh=60%" "${nixDaemonMemoryLimitDropinPath}" 2>/dev/null \
      && grep -q "MemoryMax=75%" "${nixDaemonMemoryLimitDropinPath}" 2>/dev/null; then
      $VERBOSE_ECHO "nix-daemon memory limit already configured"
    else
      echo "Setting up nix-daemon memory limits (requires sudo)..."
      sudo mkdir -p "$(dirname "${nixDaemonMemoryLimitDropinPath}")"
      printf '%s' '${nixDaemonMemoryLimitDropinContent}' | sudo tee "${nixDaemonMemoryLimitDropinPath}" > /dev/null
      sudo systemctl daemon-reload
      sudo systemctl restart nix-daemon
    fi
  '';
}
