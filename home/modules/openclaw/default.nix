{ ... }:
{
  imports = [
    ./install.nix
    ./config.nix
    ./grid.nix
    ./private.nix
    ./config-patch.nix
    ./config-patch-defaults.nix
    ./workspace.nix
    ./directories.nix
    ./skills.nix
    ./scripts.nix
    ./tts.nix
  ];
}
