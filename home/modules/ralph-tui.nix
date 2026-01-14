# Ralph TUI - AI agent workflow manager
# Connects AI coding assistants to task trackers in autonomous loops
# https://github.com/subsy/ralph-tui
{ pkgs, lib, config, ... }:
{
  # Ensure bun is available (should be in pkgs.nix)
  home.packages = with pkgs; [ bun ];

  # Install ralph-tui globally via bun on activation
  home.activation.installRalphTui = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    export PATH="${pkgs.bun}/bin:$PATH"
    if ! command -v ralph-tui &> /dev/null; then
      ${pkgs.bun}/bin/bun install -g ralph-tui 2>/dev/null || true
    fi
  '';

  # Shell alias for quick access
  programs.bash.shellAliases = {
    ralph = "ralph-tui";
    ralph-setup = "ralph-tui setup";
    ralph-run = "ralph-tui run";
    ralph-prd = "ralph-tui create-prd --chat";
  };
}
