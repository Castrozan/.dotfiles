{
  pkgs,
  nodejs,
  homeDir,
  hostname,
}:
let
  figmaDeveloperMcpVersion = "0.13.2";
  figmaPersonalAccessTokenPath = "${homeDir}/.secrets/figma-personal-access-token-${hostname}";
  figmaReadImageDownloadDirectory = "${homeDir}/.cache/figma-developer-mcp-images";

  figmaReadMcpStdioWrapper = pkgs.writeShellScript "figma-read-mcp" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:$PATH"
    FIGMA_API_KEY="$(cat ${figmaPersonalAccessTokenPath})"
    export FIGMA_API_KEY
    mkdir -p ${figmaReadImageDownloadDirectory}
    exec ${nodejs}/bin/npx -y figma-developer-mcp@${figmaDeveloperMcpVersion} \
      --stdio --no-telemetry --image-dir ${figmaReadImageDownloadDirectory}
  '';
in
{
  figmaReadMcpStdioCommand = figmaReadMcpStdioWrapper;
  figmaReadMcpStdioArgs = [ ];

  figmaWriteCapableRemoteServerConfig = {
    type = "http";
    url = "https://mcp.figma.com/mcp";
  };
}
