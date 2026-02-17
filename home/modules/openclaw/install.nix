{ pkgs, config, ... }:
let
  nodejs = pkgs.nodejs_22;
  version = "2026.2.15";
  npmPrefix = "$HOME/.local/share/openclaw-npm";

  installOpenclawViaNpm = pkgs.writeShellScript "openclaw-install" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:${pkgs.git}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${npmPrefix}"
    BIN="${npmPrefix}/bin/openclaw"

    if [ -x "$BIN" ] && [ "$("$BIN" --version 2>/dev/null)" = "${version}" ]; then
      echo "[openclaw-install] Already at ${version}, skipping"
      exit 0
    fi

    echo "[openclaw-install] Installing OpenClaw ${version}..."
    ${nodejs}/bin/npm install -g "openclaw@${version}" \
      --prefix "${npmPrefix}" --ignore-scripts
    echo "[openclaw-install] Done"
  '';

  openclawWrapper = pkgs.writeShellScriptBin "openclaw" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${npmPrefix}"
    export OPENCLAW_NIX_MODE=1
    exec "${npmPrefix}/bin/openclaw" "$@"
  '';

  browserUse = pkgs.writeShellScriptBin "browser-use" ''
    exec ${pkgs.uv}/bin/uvx browser-use[cli] "$@"
  '';
in
{
  home.packages = [
    openclawWrapper
    browserUse
    nodejs
    pkgs.uv
    pkgs.moreutils
  ];

  home.activation.installOpenclawViaNpm = config.lib.dag.entryAfter [ "writeBoundary" ] ''
    run ${installOpenclawViaNpm}
  '';
}
