{ inputs, ... }:
{
  imports = [
    inputs.clawde.homeManagerModules.default
    ./shared-herdr-server-memory-ceiling.nix
    ./wiring.nix
    ./harnesses.nix
    ./discord-channel-access.nix
    ./agent-skill-sets.nix
  ];
}
