{ ... }:
{
  imports = [
    ./interfaces.nix
    ./options.nix
    ./workspace-files.nix
    ./activations.nix
    ./service.nix
    ./channel-adapters/discord
    ./channel-adapters/pm
    ./peer-adapters/a2a
  ];
}
