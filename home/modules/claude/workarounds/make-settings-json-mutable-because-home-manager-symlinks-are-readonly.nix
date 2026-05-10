{ pkgs, ... }:
{
  home.activation.seedClaudeSettingsAsMutableFile = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
      CLAUDE_SETTINGS="$HOME/.claude/settings.json"
      NIX_SOURCE="$HOME/.claude/settings.json.nix-source"
      if [ -f "$NIX_SOURCE" ]; then
        if [ -f "$CLAUDE_SETTINGS" ]; then
          chmod 600 "$CLAUDE_SETTINGS" 2>/dev/null || true
          MERGED_SETTINGS=$(${pkgs.jq}/bin/jq -s '.[0] * .[1]' "$CLAUDE_SETTINGS" "$NIX_SOURCE")
          CURRENT_SETTINGS=$(cat "$CLAUDE_SETTINGS")
          if [ "$MERGED_SETTINGS" != "$CURRENT_SETTINGS" ]; then
            echo "$MERGED_SETTINGS" > "$CLAUDE_SETTINGS.tmp" && mv "$CLAUDE_SETTINGS.tmp" "$CLAUDE_SETTINGS"
          fi
        else
          cp "$NIX_SOURCE" "$CLAUDE_SETTINGS"
        fi
        chmod 600 "$CLAUDE_SETTINGS"
      fi
    '';
  };
}
