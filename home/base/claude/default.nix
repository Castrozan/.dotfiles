{ inputs, ... }:
{
  imports = [
    ./binary.nix
    inputs.clawde.homeManagerModules.default
    ./clawde-wiring.nix
    ./settings
    ./skill-injection
    ./workflows
    ./hooks
    ./mcps
    ./private.nix
    ./scripts
  ];
}
