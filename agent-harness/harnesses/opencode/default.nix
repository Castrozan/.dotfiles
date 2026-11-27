{ ... }:
{
  imports = [
    ./opencode.nix
    ./config.nix
    ./instructions/global-instructions.nix
    ./tui.nix
    ./agents/subagents.nix
    ./private.nix
    ../../../agent-harness/hooks/integrations/opencode/opencode-hooks-home-manager.nix
  ];
}
