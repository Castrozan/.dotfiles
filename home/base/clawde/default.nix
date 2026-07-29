{ inputs, ... }:
{
  imports = [
    inputs.clawde.homeManagerModules.default
    ./wiring.nix
    ./harnesses.nix
    ./discord-channel-access.nix
    ./agent-skill-sets.nix
  ];
}
