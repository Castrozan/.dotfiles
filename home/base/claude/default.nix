{ inputs, ... }:
{
  imports = [
    ./binary.nix
    ./config-dir-launchers.nix
    ./gpt-proxy
    inputs.clawde.homeManagerModules.default
    ./clawde-wiring.nix
    ./clawde-discord-channel-access.nix
    ./clawde-agent-skill-sets.nix
    ./settings
    ./telemetry
    ./skill-injection
    ./commands
    ./subagents
    ./workflows
    ./hooks
    ./mcps
    ./private.nix
    ./scripts
  ];
}
