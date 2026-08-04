{ inputs, ... }:
{
  imports = [
    inputs.clawde.homeManagerModules.default
    ./agent-fleet-memory-ceiling.nix
    ./wiring.nix
    ./harnesses.nix
    ./discord-channel-access.nix
    ./agent-skill-sets.nix
  ];
}
