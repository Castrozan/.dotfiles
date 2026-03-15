{ pkgs, config, ... }:
let
  chromeDevtoolsMcp = pkgs.callPackage ../browser/chrome-devtools-mcp-package.nix { };
  chromePath = "${pkgs.chromium}/bin/chromium";
  homeDir = config.home.homeDirectory;
  mcpConfig = {
    mcpServers = {
      chrome-devtools-live = {
        command = "${chromeDevtoolsMcp}/bin/chrome-devtools-mcp";
        args = [
          "--autoConnect"
          "--usageStatistics"
          "false"
        ];
      };
      chrome-devtools-headless = {
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
        command = "${homeDir}/.local/bin/scrapling-mcp";
        args = [ ];
      };
      codex = {
        command = "${homeDir}/.local/bin/codex";
        args = [ "mcp-server" ];
      };
    };
  };
in
{
  home.file.".claude/mcp.json".text = builtins.toJSON mcpConfig;
}
