{
  pkgs,
  nodejs,
  chromeDevtoolsMcpNpmPrefix,
}:
let
  chromeDevtoolsMcpVersion = "0.20.3";
in
{
  installChromeDevtoolsMcpViaNpm = pkgs.writeShellScript "install-chrome-devtools-mcp" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${chromeDevtoolsMcpNpmPrefix}"

    PACKAGE_JSON="${chromeDevtoolsMcpNpmPrefix}/lib/node_modules/chrome-devtools-mcp/package.json"

    if [ -f "$PACKAGE_JSON" ] && grep -q '"version": "${chromeDevtoolsMcpVersion}"' "$PACKAGE_JSON"; then
      exit 0
    fi

    install_npm_package() {
      ${nodejs}/bin/npm install -g "chrome-devtools-mcp@${chromeDevtoolsMcpVersion}" \
        --prefix "${chromeDevtoolsMcpNpmPrefix}" \
        --registry "https://registry.npmjs.org/" \
        --prefer-offline \
        --no-audit \
        --no-fund \
        2>&1
    }

    if ! OUTPUT=$(install_npm_package); then
      echo "npm install chrome-devtools-mcp@${chromeDevtoolsMcpVersion} failed (attempt 1), retrying..." >&2
      sleep 2
      if ! OUTPUT=$(install_npm_package); then
        echo "npm install chrome-devtools-mcp@${chromeDevtoolsMcpVersion} failed after retry: $OUTPUT" >&2
        exit 1
      fi
    fi
  '';
}
