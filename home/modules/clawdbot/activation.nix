# OpenClaw activation script — merges Nix base config with runtime config
#
# Strategy: Nix-managed keys always win, but runtime-only keys are preserved.
# This means:
#   - Keys defined in base.json overwrite the same keys in runtime config
#   - Keys only in runtime config (e.g. added via `openclaw config.patch`) survive rebuilds
#   - New keys added to base.json appear in the merged config automatically
#
# Uses jq `*` (recursive merge) with base ON TOP of runtime: runtime * base
{ pkgs, ... }:
{
  home.activation.mergeOpenClawConfig = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
      BASE="$HOME/.openclaw/openclaw.base.json"
      RUNTIME="$HOME/.openclaw/openclaw.json"
      mkdir -p "$HOME/.openclaw"

      if [ -f "$RUNTIME" ]; then
        # Deep merge: start with runtime (preserves runtime-only keys),
        # then overlay base (Nix wins on any key it defines)
        ${pkgs.jq}/bin/jq -s '.[0] * .[1]' "$RUNTIME" "$BASE" > "$RUNTIME.tmp" && mv "$RUNTIME.tmp" "$RUNTIME"
      else
        cp "$BASE" "$RUNTIME"
      fi

      # Clean up legacy clawdbot config if it exists
      if [ -f "$HOME/.clawdbot/clawdbot.json" ] && [ -f "$RUNTIME" ]; then
        # Migrate any runtime-only keys from legacy config, then remove
        ${pkgs.jq}/bin/jq -s '.[0] * .[1] * .[2]' \
          "$HOME/.clawdbot/clawdbot.json" "$RUNTIME" "$BASE" \
          > "$RUNTIME.tmp" && mv "$RUNTIME.tmp" "$RUNTIME"
        rm -f "$HOME/.clawdbot/clawdbot.json" "$HOME/.clawdbot/clawdbot.base.json"
        rmdir "$HOME/.clawdbot" 2>/dev/null || true
      fi
    '';
  };
}
