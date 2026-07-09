{ inputs, ... }:
{
  imports = [
    ./binary.nix
    inputs.clawde.homeManagerModules.default
    ./clawde-wiring.nix
    ./clawde-discord-channel-access.nix
    ./settings
    ./telemetry
    ./skill-injection
    ./commands
    ./workflows
    ./hooks
    ./mcps
    ./private.nix
    ./scripts
  ];
}
