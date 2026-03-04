{ pkgs, ... }:
let
  nodePath = "${pkgs.nodejs_22}/bin";
  chromePath = "${pkgs.chromium}/bin/chromium";
  mcpConfig = {
    mcpServers = {
      chrome-devtools = {
        command = "${nodePath}/npx";
        args = [
          "chrome-devtools-mcp@latest"
          "--headless"
          "--executablePath"
          chromePath
          "--usageStatistics"
          "false"
        ];
      };
      scrapling-fetch = {
        command = "/home/lucas.zanoni/.local/bin/scrapling-mcp";
        args = [ ];
      };
    };
  };
in
{
  home.file.".claude/mcp.json".text = builtins.toJSON mcpConfig;
}
