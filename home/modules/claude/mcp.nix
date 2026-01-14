{ pkgs, lib, ... }:
let
  mcpConfig = {
    mcpServers = {
      claudemem = {
        command = "npx";
        args = [ "claude-codemem" "serve" ];
      };

    };
  };
in
{
  home.file.".claude/mcp.json".text = builtins.toJSON mcpConfig;
}
