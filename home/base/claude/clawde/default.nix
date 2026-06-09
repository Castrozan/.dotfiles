{ ... }:
{
  imports = [
    ./interfaces.nix
    ./agent-type-interfaces.nix
    ./options.nix
    ./agent-assertions.nix
    ./agent-types
    ./host-identity.nix
    ./fleet.nix
    ./workspace-files.nix
    ./instruction-files.nix
    ./launch-config-files.nix
    ./activations.nix
    ./service.nix
    ./channel-adapters/discord
    ./channel-adapters/pm
    ./peer-adapters/a2a
    ./health.nix
  ];
}
