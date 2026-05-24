{
  pkgs,
  config,
  lib,
  ...
}:
let
  nodejs = pkgs.nodejs_22;
  homeDir = config.home.homeDirectory;
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

    ${nodejs}/bin/npm install -g "a2a-mcp-server@${a2aMcpServerVersion}" \
      --prefix "${a2aMcpServerNpmPrefix}" \
      --registry "https://registry.npmjs.org/"
  '';

  a2aMcpServerToInject = builtins.toJSON {
    a2a = {
      command = "${nodejs}/bin/node";
      args = [ a2aMcpServerBinary ];
    };
  };

  injectA2aMcpServerIntoClaudeConfig = pkgs.writeShellScript "inject-a2a-mcp-server" ''
    set -euo pipefail
    CLAUDE_CONFIG="${homeDir}/.claude.json"
    SERVERS='${a2aMcpServerToInject}'

    if [ ! -f "$CLAUDE_CONFIG" ]; then
      echo '{"mcpServers":{}}' > "$CLAUDE_CONFIG"
    fi

    ${pkgs.jq}/bin/jq --argjson servers "$SERVERS" '.mcpServers = (.mcpServers // {}) * $servers' "$CLAUDE_CONFIG" | ${pkgs.moreutils}/bin/sponge "$CLAUDE_CONFIG"
  '';
in
{
  home.activation = {
    installA2aMcpServer = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${installA2aMcpServerViaNpm}
    '';

    injectA2aMcpServer = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${injectA2aMcpServerIntoClaudeConfig}
    '';
  };
}
