# --ignore-scripts skips node-llama-cpp cmake build (unused).
{ pkgs, ... }:
let
  nodejs = pkgs.nodejs_22;
  version = "2026.2.9";
  prefix = "$HOME/.local/share/openclaw-npm";

  openclaw = pkgs.writeShellScriptBin "openclaw" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${prefix}"
    BIN="${prefix}/bin/openclaw"

    if [ ! -x "$BIN" ] || [ "$("$BIN" --version 2>/dev/null)" != "${version}" ]; then
      echo "[nix] Installing OpenClaw ${version}..." >&2
      ${nodejs}/bin/npm install -g "openclaw@${version}" \
        --prefix "${prefix}" --ignore-scripts >&2
    fi

    exec "$BIN" "$@"
  '';

  browserUse = pkgs.writeShellScriptBin "browser-use" ''
    exec ${pkgs.uv}/bin/uvx browser-use[cli] "$@"
  '';
in
{
  home.packages = [
    openclaw
    browserUse
    nodejs
    pkgs.uv
  ];
}
