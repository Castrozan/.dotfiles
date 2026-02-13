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
  ];

  _module.args.isNixOS = lib.mkDefault false;
}
