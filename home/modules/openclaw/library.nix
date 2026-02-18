{ lib, ... }:
{
  imports = [
    ./config.nix
    ./config-patch.nix
    ./config-patch-defaults.nix
    ./directories.nix
    ./install.nix
    ./gateway-service.nix
    ./memory-sync.nix
    ./plugins.nix
    ./hindsight-fixups.nix
  ];

  _module.args.isNixOS = lib.mkDefault false;
}
