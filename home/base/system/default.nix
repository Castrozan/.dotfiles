{
  imports = [
    ../../linux/system/ipv6-disabled.nix
    ../../linux/system/lid-switch-ignore.nix
    ../../linux/system/oom-protection.nix
    ../../linux/system/ubuntu-system-tuning.nix
    ./scripts.nix
    ./stale-symlink-cleanup.nix
  ];
}
