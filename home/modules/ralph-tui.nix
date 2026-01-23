# Ralph TUI - AI agent workflow manager
# Connects AI coding assistants to task trackers in autonomous loops
# https://github.com/subsy/ralph-tui
{ pkgs, lib, ... }:
{
  home = {
    # Ensure bun is available (should be in pkgs.nix)
    packages = with pkgs; [ bun ];

    # Add bun global bin to PATH
    sessionPath = [ "$HOME/.bun/bin" ];

    # Install ralph-tui globally via bun on activation
    activation.installRalphTui = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      export PATH="${pkgs.bun}/bin:$PATH"
      if [ ! -f "$HOME/.bun/bin/ralph-tui" ]; then
        ${pkgs.bun}/bin/bun install -g ralph-tui 2>/dev/null || true
      fi
    '';
  };

  # Shell alias for quick access
  programs.bash.shellAliases = {
    ralph = "ralph-tui";
    ralph-setup = "ralph-tui setup";
    ralph-run = "ralph-tui run";
    ralph-prd = "ralph-tui create-prd --chat";
  };
}
