{ lib, ... }:
{
  imports = [
    ./config-options.nix
    ./config-engine.nix
    ./config-declarations.nix
    ./workspace-dirs.nix
    ./install.nix
    ./systemd-service.nix
    ./health-check.nix
    ./restart-watcher.nix
    ./ensure-services-after-rebuild.nix
    ./plugins/memory-sync.nix
    ./plugins/plugins.nix
  ];

  _module.args.isNixOS = lib.mkDefault false;
}
