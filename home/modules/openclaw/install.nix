# OpenClaw package — pinned version, npm install into Nix-managed prefix
#
# Version bumps: change `version` and rebuild.
# The wrapper auto-installs if missing or outdated.
# --ignore-scripts skips node-llama-cpp cmake build (unused).
{ pkgs, ... }:
let
  nodejs = pkgs.nodejs_22;
  version = "2026.1.30";
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

  clawdbot = pkgs.writeShellScriptBin "clawdbot" ''
    exec ${openclaw}/bin/openclaw "$@"
  '';
in
{
  home.packages = [
    openclaw
    clawdbot
    nodejs
  ];
}
