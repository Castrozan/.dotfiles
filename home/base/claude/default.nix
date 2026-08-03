{ ... }:
{
  imports = [
    ./binary.nix
    ./config-dir-launchers.nix
    ./gpt-proxy
    ./settings
    ./telemetry
    ./skill-injection
    ./commands
    ./subagents
    ./workflows
    ./hooks
    ./mcps
    ./opencode-go
    ./private.nix
    ./scripts
  ];
}
