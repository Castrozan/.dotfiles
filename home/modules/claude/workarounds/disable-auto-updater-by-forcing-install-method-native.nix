{ pkgs, ... }:
{
  home.activation.patchClaudeJsonInstallMethod = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
      CLAUDE_JSON="$HOME/.claude.json"
      if [ -f "$CLAUDE_JSON" ]; then
        if ! ${pkgs.jq}/bin/jq '.' "$CLAUDE_JSON" >/dev/null 2>&1; then
          echo "WARNING: $CLAUDE_JSON is corrupt, skipping patch" >&2
        else
          PATCHED_CONTENT=$(${pkgs.jq}/bin/jq '.installMethod = "native"' "$CLAUDE_JSON")
          CURRENT_CONTENT=$(cat "$CLAUDE_JSON")
          if [ "$PATCHED_CONTENT" != "$CURRENT_CONTENT" ]; then
            echo "$PATCHED_CONTENT" > "$CLAUDE_JSON.tmp" && mv "$CLAUDE_JSON.tmp" "$CLAUDE_JSON"
          fi
        fi
      else
        echo '{"installMethod": "native"}' > "$CLAUDE_JSON"
      fi
    '';
  };
}
