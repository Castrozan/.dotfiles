{ pkgs, lib, ... }:
let
  # MCP server configuration
  # Add new MCP servers here following the pattern
  mcpConfig = {
    mcpServers = {
      # claudemem - memory/context persistence for Claude Code
      # Install: npm install -g claude-codemem (if available)
      # Or use npx: change command to "npx" and args to ["claude-codemem", "serve"]
      claudemem = {
        command = "npx";
        args = [ "claude-codemem" "serve" ];
      };

    };
  };
in
{
  # MCP configuration file
  home.file.".claude/mcp.json".text = builtins.toJSON mcpConfig;
}
