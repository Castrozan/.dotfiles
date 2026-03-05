{ pkgs, lib, ... }:
let
  patchScript = ./patch.py;
  codexDefaultModel = "gpt-5.4";
  patchScriptHash = builtins.hashFile "sha256" patchScript;
  patchScriptBaselineSignature = "${patchScriptHash}:${codexDefaultModel}";
in
{
  home.file.".codex/.baseline-hash".text = patchScriptBaselineSignature;

  home.activation.codexBaselineConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    MARKER="$HOME/.codex/.baseline-applied"
    EXPECTED="${patchScriptBaselineSignature}"

    if [ ! -f "$MARKER" ] || [ "$(cat "$MARKER" 2>/dev/null)" != "$EXPECTED" ]; then
      CODEX_DEFAULT_MODEL="${codexDefaultModel}" ${pkgs.python3}/bin/python3 ${patchScript}
      echo "$EXPECTED" > "$MARKER"
    fi
  '';
}
