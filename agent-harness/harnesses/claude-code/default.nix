{ ... }:
{
  imports = [
    ./launch/claude-binary-package.nix
    ./model-providers/chatgpt-subscription
    ./settings
    ../../../agent-harness/measurement-and-reporting/claude-telemetry/claude-telemetry-home-manager.nix
    ./skills/global-skills-home-manager.nix
    ./launch/interactive-claude-command.nix
    ./skills/runtime-packages-home-manager.nix
    ./subagents
    ./workflows
    ../../../agent-harness/hooks/integrations/claude/claude-hooks-home-manager.nix
    ./mcps
    ./model-providers/opencode-go
    ./plugins/automatic-updates-home-manager.nix
    ./private.nix
    ./scripts
    ../../workspace-profiles
  ];
}
