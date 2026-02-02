{ ... }:
{
  imports = [
    ./install.nix
    ./config.nix
    ./config-patch.nix
    ./workspace.nix
    ./directories.nix
    ./rules.nix
    ./skills.nix
    ./scripts.nix
    ./tts.nix
  ];
}
