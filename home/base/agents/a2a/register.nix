{
  pkgs,
  homeDir,
  nodejs ? pkgs.nodejs_22,
}:
let
  a2aMcpServer = import ./install.nix {
    inherit pkgs homeDir nodejs;
  };

  a2aMcpServerStdioSpec = {
    command = a2aMcpServer.mcpServerCommand;
    args = a2aMcpServer.mcpServerArgs;
  };

  registerStdioServerInJsonConfig =
    {
      providerConfigPath,
      serverKey ? "a2a",
    }:
    let
      serversJson = builtins.toJSON {
        ${serverKey} = a2aMcpServerStdioSpec;
      };
    in
    pkgs.writeShellScript "register-a2a-mcp-server-in-${baseNameOf providerConfigPath}" ''
      set -euo pipefail
      PROVIDER_CONFIG="${providerConfigPath}"
      SERVERS='${serversJson}'

      if [ ! -f "$PROVIDER_CONFIG" ]; then
        echo '{"mcpServers":{}}' > "$PROVIDER_CONFIG"
      fi

      ${pkgs.jq}/bin/jq --argjson servers "$SERVERS" \
        '.mcpServers = (.mcpServers // {}) * $servers' \
        "$PROVIDER_CONFIG" | ${pkgs.moreutils}/bin/sponge "$PROVIDER_CONFIG"
    '';
in
{
  inherit (a2aMcpServer) binary mcpServerCommand mcpServerArgs;
  inherit a2aMcpServerStdioSpec registerStdioServerInJsonConfig;
}
