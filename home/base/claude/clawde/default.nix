{ ... }:
{
  imports = [
    ./interfaces.nix
    ./agent-type-interfaces.nix
    ./host-wiring-interfaces.nix
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
    ./peer-adapters/a2a
    ./health.nix
  ];
}
