{ ... }:
{
  imports = [
    ./interfaces.nix
    ./options.nix
    ./host-identity.nix
    ./fleet.nix
    ./workspace-files.nix
    ./instruction-files.nix
    ./activations.nix
    ./service.nix
    ./channel-adapters/discord
    ./channel-adapters/pm
    ./peer-adapters/a2a
    ./health.nix
  ];
}
