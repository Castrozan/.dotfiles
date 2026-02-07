{ ... }:
{
  imports = [
    ./config.nix
    ./deploy.nix
    ./grid.nix
    ./config-patch.nix
    ./config-patch-defaults.nix
    ./directories.nix
    ./install.nix
    ./avatar.nix
  ];
}
