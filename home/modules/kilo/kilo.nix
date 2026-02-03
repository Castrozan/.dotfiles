# Kilo Code CLI - AI coding assistant
# https://kilo.ai
{ pkgs, config, ... }:
let
  nodejs = pkgs.nodejs_22;
  prefix = "$HOME/.local/share/kilo-npm";

  # Auto-installing wrapper that ensures the CLI is available
  kilo = pkgs.writeShellScriptBin "kilo" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${prefix}"
    BIN="${prefix}/bin/kilo"

    # Install if missing
    if [ ! -x "$BIN" ]; then
      echo "[nix] Installing Kilo Code CLI..." >&2
      ${nodejs}/bin/npm install -g "@kilocode/cli" \
        --prefix "${prefix}" >&2
    fi

    exec "$BIN" "$@"
  '';
in
{
  home.packages = [ kilo ];
}
