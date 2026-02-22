{ pkgs, config, ... }:
let
  nodejs = pkgs.nodejs_22;
  version = "2026.2.19-2";
  npmPrefix = "$HOME/.local/share/openclaw-npm";
  secretsDirectory = "${config.home.homeDirectory}/.secrets";

  installOpenclawViaNpm = pkgs.writeShellScript "openclaw-install" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:${pkgs.git}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${npmPrefix}"
    BIN="${npmPrefix}/bin/openclaw"

    if [ -x "$BIN" ] && [ "$("$BIN" --version 2>/dev/null)" = "${version}" ]; then
      exit 0
    fi

    ${nodejs}/bin/npm install -g "openclaw@${version}" \
      --prefix "${npmPrefix}" \
      --ignore-scripts
  '';

  openclawWrapper = pkgs.writeShellScriptBin "openclaw" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${npmPrefix}"
    export OPENCLAW_NIX_MODE=1
    unset CLAUDECODE
    if [ -f "${secretsDirectory}/gemini-api-key" ]; then
      GEMINI_API_KEY="$(cat "${secretsDirectory}/gemini-api-key")"
      export GEMINI_API_KEY
    fi
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
