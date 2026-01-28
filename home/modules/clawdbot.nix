# clawdbot - Personal AI assistant
# https://github.com/moltbot/moltbot
# https://clawd.bot
{ pkgs, ... }:
let
  nodejs = pkgs.nodejs_22;

  clawdbot = pkgs.writeShellScriptBin "clawdbot" ''
    export PATH="${nodejs}/bin:$PATH"
    CLAWDBOT_DIR="$HOME/.clawdbot"

    if [ ! -d "$CLAWDBOT_DIR" ]; then
      echo "Installing clawdbot..."
      ${pkgs.curl}/bin/curl -fsSL https://molt.bot/install.sh | ${pkgs.bash}/bin/bash
    fi

    if [ -x "$HOME/.local/bin/clawdbot" ]; then
      exec "$HOME/.local/bin/clawdbot" "$@"
    elif [ -x "$CLAWDBOT_DIR/moltbot.mjs" ]; then
      exec ${nodejs}/bin/node "$CLAWDBOT_DIR/moltbot.mjs" "$@"
    else
      echo "clawdbot not found. Running installer..."
      ${pkgs.curl}/bin/curl -fsSL https://molt.bot/install.sh | ${pkgs.bash}/bin/bash
      exec "$HOME/.local/bin/clawdbot" "$@"
    fi
  '';
in
{
  home.packages = [
    clawdbot
    nodejs
  ];
}
