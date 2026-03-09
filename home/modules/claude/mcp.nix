{ pkgs, ... }:
let
  chromeDevtoolsMcp = pkgs.callPackage ../browser/chrome-devtools-mcp-package.nix { };
  chromePath = "${pkgs.chromium}/bin/chromium";
  mcpConfig = {
    mcpServers = {
      chrome-devtools = {
        command = "${chromeDevtoolsMcp}/bin/chrome-devtools-mcp";
        args = [
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
