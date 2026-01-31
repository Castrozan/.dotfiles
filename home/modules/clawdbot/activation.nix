# OpenClaw activation script — merges base config with runtime config
{ pkgs, ... }:
{
  home.activation.mergeClawdbotConfig = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
      BASE="$HOME/.clawdbot/clawdbot.base.json"
      RUNTIME="$HOME/.clawdbot/clawdbot.json"
      mkdir -p "$HOME/.clawdbot"
      if [ -f "$RUNTIME" ]; then
        ${pkgs.jq}/bin/jq -s '.[1] * .[0]' "$RUNTIME" "$BASE" > "$RUNTIME.tmp" && mv "$RUNTIME.tmp" "$RUNTIME"
      else
        cp "$BASE" "$RUNTIME"
      fi
    '';
  };
}
