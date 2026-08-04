{ ... }:
{
  imports = [
    ./opencode.nix
    ./config.nix
    ./global-instructions.nix
    ./tui.nix
    ./skills.nix
    ./subagents.nix
    ./commands.nix
    ./private.nix
    ./hooks.nix
  ];
}
