{ ... }:
{
  imports = [
    ./opencode.nix
    ./config.nix
    ./global-instructions.nix
    ./tui.nix
    ./skills.nix
    ./subagents.nix
    ./private.nix
    ../../workspace-profiles
    ../../../agent-harness/hooks/integrations/opencode/opencode-hooks-home-manager.nix
  ];
}
