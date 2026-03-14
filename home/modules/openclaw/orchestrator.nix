{ lib, ... }:
{
  imports = [
    ./config-options.nix
    ./config-engine.nix
    ./config-declarations.nix
    ./workspace-dirs.nix
    ./install.nix
    ./systemd-service.nix
    ./reliability/health-check.nix
    ./reliability/scheduled-backup.nix
    ./reliability/restart-watcher/restart-watcher.nix
    ./reliability/timeout-recovery.nix
    ./reliability/restart-watcher/ensure-services-after-rebuild.nix
    ./plugins/memory-sync.nix
    ./plugins/plugins.nix
  ];

  _module.args.isNixOS = lib.mkDefault false;
}
