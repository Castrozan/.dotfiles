{ ... }:
{
  imports = [
    ./binary.nix
    ./config-dir-launchers.nix
    ./gpt-proxy
    ./settings
    ../../../agent-harness/measurement-and-reporting/claude-telemetry/claude-telemetry-home-manager.nix
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
