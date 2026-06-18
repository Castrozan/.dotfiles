{
  lib,
  latest,
  ...
}:
let
  bunPackage = latest.bun;
in
{
  home = {
    sessionPath = [ "$HOME/.bun/bin" ];

    activation.installWahaTui = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      export PATH="${bunPackage}/bin:$PATH"
      if [ ! -f "$HOME/.bun/bin/waha-tui" ]; then
        ${bunPackage}/bin/bun install -g @muhammedaksam/waha-tui 2>/dev/null || true
      fi
    '';
  };
}
