{
  pkgs,
  lib,
  latest,
  ...
}:
let
  # ralph-tui >=0.x requires Bun >=1.3.6; nixpkgs stable currently pins 1.3.3,
  # so use the daily-bumped nixpkgs-latest channel for bun specifically.
  bunPackage = latest.bun;
in
{
  home = {
    sessionPath = [ "$HOME/.bun/bin" ];

    activation.installRalphTui = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      export PATH="${bunPackage}/bin:$PATH"
      if [ ! -f "$HOME/.bun/bin/ralph-tui" ]; then
        ${bunPackage}/bin/bun install -g ralph-tui 2>/dev/null || true
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
