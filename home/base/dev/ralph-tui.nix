{ pkgs, lib, ... }:
{
  home = {
    packages = with pkgs; [ bun ];

    sessionPath = [ "$HOME/.bun/bin" ];

    activation.installRalphTui = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      export PATH="${pkgs.bun}/bin:$PATH"
      if [ ! -f "$HOME/.bun/bin/ralph-tui" ]; then
        ${pkgs.bun}/bin/bun install -g ralph-tui 2>/dev/null || true
      fi
    '';
  };

  programs.bash.shellAliases = {
    ralph = "ralph-tui";
    ralph-setup = "ralph-tui setup";
    ralph-run = "ralph-tui run";
    ralph-prd = "ralph-tui create-prd --chat";
  };
}
