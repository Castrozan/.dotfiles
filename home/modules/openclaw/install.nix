{ pkgs, config, ... }:
let
  nodejs = pkgs.nodejs_22;
  version = "2026.2.15";
  prefix = "$HOME/.local/share/openclaw-npm";

  openclaw = pkgs.writeShellScriptBin "openclaw" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${prefix}"
    export OPENCLAW_NIX_MODE=1
    BIN="${prefix}/bin/openclaw"

    if [ ! -x "$BIN" ] || [ "$("$BIN" --version 2>/dev/null)" != "${version}" ]; then
      echo "[nix] Installing OpenClaw ${version}..." >&2
      ${nodejs}/bin/npm install -g "openclaw@${version}" \
        --prefix "${prefix}" --ignore-scripts >&2
      ${config.openclaw.sessionPathPatchScript}
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
