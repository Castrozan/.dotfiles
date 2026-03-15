{
  pkgs,
  config,
  latest,
  ...
}:
let
  chromeDevtoolsMcp = pkgs.callPackage ../browser/chrome-devtools-mcp-package.nix { };
  googleChromePath = "${latest.google-chrome}/bin/google-chrome-stable";
  homeDir = config.home.homeDirectory;
  mcpConfig = {
    mcpServers = {
      chrome-devtools = {
        command = "${chromeDevtoolsMcp}/bin/chrome-devtools-mcp";
        args = [
          "--autoConnect"
          "--executablePath"
          googleChromePath
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
  home.packages = [ latest.google-chrome ];
  home.file.".claude/mcp.json".text = builtins.toJSON mcpConfig;
}
