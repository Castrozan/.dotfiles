{ pkgs, ... }:
let
  chromePath = "${pkgs.google-chrome}/bin/google-chrome-stable";
  mcpConfig = {
    mcpServers = {
      playwright = {
        command = "npx";
        args = [
          "@playwright/mcp@latest"
          "--headless"
          "--executable-path"
          chromePath
        ];
      };
    };
  };
in
{
  home.file.".claude/mcp.json".text = builtins.toJSON mcpConfig;
}
