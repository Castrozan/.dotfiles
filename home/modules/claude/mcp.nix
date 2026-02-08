{ pkgs, ... }:
let
  chromePath = "${pkgs.chromium}/bin/chromium";
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
