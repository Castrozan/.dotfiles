# OpenClaw package installation — wrapper scripts and nodejs
{ pkgs, ... }:
let
  nodejs = pkgs.nodejs_22;

  # OpenClaw wrapper — prefers npm-global install, falls back to installer
  openclaw = pkgs.writeShellScriptBin "openclaw" ''
    export PATH="${nodejs}/bin:$PATH"
    export NPM_CONFIG_PREFIX="$HOME/.npm-global"
    OPENCLAW_DIR="$HOME/.openclaw"
    NPM_BIN="$HOME/.npm-global/bin/openclaw"
    LEGACY_NPM_BIN="$HOME/.npm-global/bin/clawdbot"

    if [ -x "$NPM_BIN" ]; then
      exec "$NPM_BIN" "$@"
    elif [ -x "$LEGACY_NPM_BIN" ]; then
      exec "$LEGACY_NPM_BIN" "$@"
    elif [ -x "$OPENCLAW_DIR/openclaw.mjs" ]; then
      exec ${nodejs}/bin/node "$OPENCLAW_DIR/openclaw.mjs" "$@"
    else
      echo "OpenClaw not found. Running installer..."
      ${pkgs.curl}/bin/curl -fsSL https://openclaw.ai/install.sh | ${pkgs.bash}/bin/bash
      if [ -x "$NPM_BIN" ]; then
        exec "$NPM_BIN" "$@"
      else
        exec "$HOME/.local/bin/openclaw" "$@"
      fi
    fi
  '';

  # Backwards compatibility: clawdbot → openclaw
  clawdbot = pkgs.writeShellScriptBin "clawdbot" ''
    exec ${openclaw}/bin/openclaw "$@"
  '';
in
{
  home.packages = [
    openclaw
    clawdbot # backwards compat shim
    nodejs
  ];
}
