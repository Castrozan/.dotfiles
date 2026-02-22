{ pkgs, config, ... }:
let
  nodejs = pkgs.nodejs_22;
  version = "2026.2.21-2";
  discordVoiceDavePackageVersion = "0.1.9";
  discordJsPackageVersion = "14.22.1";
  npmPrefix = "$HOME/.local/share/openclaw-npm";
  secretsDirectory = "${config.home.homeDirectory}/.secrets";

  installOpenclawViaNpm = pkgs.writeShellScript "openclaw-install" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:${pkgs.git}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${npmPrefix}"
    OPENCLAW_BIN="${npmPrefix}/bin/openclaw"
    DAVE_PACKAGE_JSON="${npmPrefix}/lib/node_modules/@snazzah/davey/package.json"
    DISCORD_JS_PACKAGE_JSON="${npmPrefix}/lib/node_modules/discord.js/package.json"

    OPENCLAW_READY=false
    if [ -x "$OPENCLAW_BIN" ] && [ "$("$OPENCLAW_BIN" --version 2>/dev/null)" = "${version}" ]; then
      OPENCLAW_READY=true
    fi

    DAVEY_READY=false
    if [ -f "$DAVE_PACKAGE_JSON" ] && grep -q '"version": "${discordVoiceDavePackageVersion}"' "$DAVE_PACKAGE_JSON"; then
      DAVEY_READY=true
    fi

    DISCORD_JS_READY=false
    if [ -f "$DISCORD_JS_PACKAGE_JSON" ] && grep -q '"version": "${discordJsPackageVersion}"' "$DISCORD_JS_PACKAGE_JSON"; then
      DISCORD_JS_READY=true
    fi

    if [ "$OPENCLAW_READY" = true ] && [ "$DAVEY_READY" = true ] && [ "$DISCORD_JS_READY" = true ]; then
      exit 0
    fi

    ${nodejs}/bin/npm install -g "openclaw@${version}" "@snazzah/davey@${discordVoiceDavePackageVersion}" "discord.js@${discordJsPackageVersion}" \
      --prefix "${npmPrefix}" \
      --ignore-scripts \
      --registry "https://registry.npmjs.org/"
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
