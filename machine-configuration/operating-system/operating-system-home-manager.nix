{
  imports = [
    ../network/ipv6/ipv6-disabled-home-manager.nix
    ./power-management/lid-switch-ignore-home-manager.nix
    ./memory-protection/oom-protection-home-manager.nix
    ./ubuntu-tuning/ubuntu-system-tuning-home-manager.nix
    ./package-management/system-command-packages-home-manager.nix
    ./storage-maintenance/nix-store/stale-symlink-cleanup-home-manager.nix
  ];
}
