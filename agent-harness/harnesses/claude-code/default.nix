{ ... }:
{
  imports = [
    ./binary.nix
    ./config-dir-launchers.nix
    ./gpt-proxy
    ./settings
    ../../../agent-harness/measurement-and-reporting/claude-telemetry/claude-telemetry-home-manager.nix
    ./skill-injection
    ./subagents
    ./workflows
    ../../../agent-harness/hooks/integrations/claude/claude-hooks-home-manager.nix
    ./mcps
    ./opencode-go
    ./private.nix
    ./scripts
  ];
}
