{ inputs, ... }:
{
  imports = [
    inputs.clawde.homeManagerModules.default
    ./peer-transport/a2a-home-manager.nix
    ./peer-transport/herdr-service-consumer.nix
    ./wiring.nix
    ./agent-enable.nix
    ./harnesses.nix
    ./discord/channel-access.nix
    ./discord/agents-allowed-to-stay-silent.nix
    ./agents-denied-destructive-commands.nix
    ./agent-skill-sets.nix
    ./agent-memory-write-tool.nix
    ./agent-media-tools.nix
  ];
}
