{
  pkgs,
  nodejs,
  homeDir,
  hostname,
}:
let
  figmaDeveloperMcpVersion = "0.13.2";
  figmaPersonalAccessTokenPath = "${homeDir}/.secrets/figma-personal-access-token-${hostname}";
  figmaMcpImageDownloadDirectory = "${homeDir}/.cache/figma-developer-mcp-images";

  figmaMcpStdioWrapper = pkgs.writeShellScript "figma-developer-mcp" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:$PATH"
    FIGMA_API_KEY="$(cat ${figmaPersonalAccessTokenPath})"
    export FIGMA_API_KEY
    mkdir -p ${figmaMcpImageDownloadDirectory}
    exec ${nodejs}/bin/npx -y figma-developer-mcp@${figmaDeveloperMcpVersion} \
      --stdio --no-telemetry --image-dir ${figmaMcpImageDownloadDirectory}
  '';
in
{
  figmaMcpStdioCommand = figmaMcpStdioWrapper;
  figmaMcpStdioArgs = [ ];
}
