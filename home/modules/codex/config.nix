{ pkgs, lib, ... }:
let
  patchScript = ./patch.py;
  patchScriptHash = builtins.hashFile "sha256" patchScript;
in
{
  home.file.".codex/.baseline-hash".text = patchScriptHash;

  home.activation.codexBaselineConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    MARKER="$HOME/.codex/.baseline-applied"
    EXPECTED="${patchScriptHash}"

    if [ ! -f "$MARKER" ] || [ "$(cat "$MARKER" 2>/dev/null)" != "$EXPECTED" ]; then
      ${pkgs.python3}/bin/python3 ${patchScript}
      echo "$EXPECTED" > "$MARKER"
    fi
  '';
}
