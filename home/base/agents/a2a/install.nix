{
  pkgs,
  homeDir,
  nodejs,
}:
let
  a2aMcpServerVersion = "1.0.0";
  a2aMcpServerNpmPrefix = "${homeDir}/.local/share/a2a-mcp-server-npm";
  a2aMcpServerBinary = "${a2aMcpServerNpmPrefix}/bin/a2a-mcp-server";

  installA2aMcpServerViaNpm = pkgs.writeShellScript "install-a2a-mcp-server" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${a2aMcpServerNpmPrefix}"

    PACKAGE_JSON="${a2aMcpServerNpmPrefix}/lib/node_modules/a2a-mcp-server/package.json"

    if [ -f "$PACKAGE_JSON" ] && grep -q '"version": "${a2aMcpServerVersion}"' "$PACKAGE_JSON"; then
      exit 0
    fi

    install_npm_package() {
      ${nodejs}/bin/npm install -g "a2a-mcp-server@${a2aMcpServerVersion}" \
        --prefix "${a2aMcpServerNpmPrefix}" \
        --registry "https://registry.npmjs.org/" \
        --prefer-offline \
        --no-audit \
        --no-fund \
        2>&1
    }

    if ! OUTPUT=$(install_npm_package); then
      echo "npm install a2a-mcp-server@${a2aMcpServerVersion} failed (attempt 1), retrying..." >&2
      sleep 2
      if ! OUTPUT=$(install_npm_package); then
        echo "npm install a2a-mcp-server@${a2aMcpServerVersion} failed after retry: $OUTPUT" >&2
        exit 1
      fi
    fi
  '';
in
{
  binary = a2aMcpServerBinary;
  installScript = installA2aMcpServerViaNpm;
  mcpServerCommand = "${nodejs}/bin/node";
  mcpServerArgs = [ a2aMcpServerBinary ];
}
