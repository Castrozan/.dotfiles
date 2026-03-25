{
  pkgs,
  homeDir,
  nodejs,
}:
let
  a2aMcpVersion = "1.0.0";
  a2aMcpNpmPrefix = "${homeDir}/.local/share/a2a-mcp-server-npm";

  installA2aMcpViaNpm = pkgs.writeShellScript "install-a2a-mcp-server" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${a2aMcpNpmPrefix}"

    PACKAGE_JSON="${a2aMcpNpmPrefix}/lib/node_modules/a2a-mcp-server/package.json"

    if [ -f "$PACKAGE_JSON" ] && grep -q '"version": "${a2aMcpVersion}"' "$PACKAGE_JSON"; then
      exit 0
    fi

    install_npm_package() {
      ${nodejs}/bin/npm install -g "a2a-mcp-server@${a2aMcpVersion}" \
        --prefix "${a2aMcpNpmPrefix}" \
        --registry "https://registry.npmjs.org/" \
        --prefer-offline \
        --no-audit \
        --no-fund \
        2>&1
    }

    if ! OUTPUT=$(install_npm_package); then
      echo "npm install a2a-mcp-server@${a2aMcpVersion} failed (attempt 1), retrying..." >&2
      sleep 2
      if ! OUTPUT=$(install_npm_package); then
        echo "npm install a2a-mcp-server@${a2aMcpVersion} failed after retry: $OUTPUT" >&2
        exit 1
      fi
    fi
  '';
in
{
  inherit installA2aMcpViaNpm;
}
