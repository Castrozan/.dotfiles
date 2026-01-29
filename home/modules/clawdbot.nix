# clawdbot - Personal AI assistant
# https://github.com/moltbot/moltbot
# https://clawd.bot
{ pkgs, lib, ... }:
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

  # Layer 1: Nix-managed workspace files (read-only symlinks)
  clawdbotDir = ../../agents/clawdbot;
  clawdbotFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir clawdbotDir)
  );
  workspaceSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "clawd/.nix/${filename}";
      value = {
        source = clawdbotDir + "/${filename}";
      };
    }) clawdbotFiles
  );
in
{
  home = {
    packages = [
      clawdbot
      nodejs
    ];
    file = workspaceSymlinks;
  };
}
