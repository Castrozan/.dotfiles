{ ... }:
{
  imports = [
    ./opencode.nix
    ./config.nix
    ./instructions/global-instructions.nix
    ./tui.nix
    ./skills.nix
    ./agents/subagents.nix
    ./claude-plugin-port.nix
    ./private.nix
    ../../workspace-profiles
    ../../../agent-harness/hooks/integrations/opencode/opencode-hooks-home-manager.nix
  ];
}
